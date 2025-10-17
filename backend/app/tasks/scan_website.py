from celery import Task
from sqlalchemy.orm import Session
from datetime import datetime
import asyncio

from app.core.celery_app import celery_app
from app.core.database import get_sync_db
from app.models import ScanSession, Page, Error, Website
from app.models.scan_session import ScanStatus
from app.models.error import ErrorType, ErrorSeverity
from app.services.crawler import CrawlerService
from app.services.spell_checker import SpellCheckerService
from app.services.address_validator import AddressValidatorService
from app.services.link_checker import LinkCheckerService
from app.services.seo_checker import SEOCheckerService


class ScanWebsiteTask(Task):
    """Custom Celery task for scanning websites."""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure."""
        scan_session_id = kwargs.get('scan_session_id')
        if scan_session_id:
            db = next(get_sync_db())
            try:
                scan_session = db.query(ScanSession).get(scan_session_id)
                if scan_session:
                    scan_session.status = ScanStatus.FAILED
                    scan_session.error_message = str(exc)
                    scan_session.completed_at = datetime.utcnow()
                    db.commit()
            finally:
                db.close()


@celery_app.task(base=ScanWebsiteTask, bind=True, name="scan_website")
def scan_website_task(self, scan_session_id: int):
    """
    Main task for scanning a website.
    
    This task:
    1. Crawls the website
    2. Runs all checks on each page
    3. Saves results to database
    """
    db = next(get_sync_db())
    
    try:
        # Get scan session
        scan_session = db.query(ScanSession).get(scan_session_id)
        if not scan_session:
            raise ValueError(f"ScanSession {scan_session_id} not found")
        
        # Update status
        scan_session.status = ScanStatus.RUNNING
        scan_session.started_at = datetime.utcnow()
        db.commit()
        
        # Get website
        website = scan_session.website
        preferences = website.preferences or {}
        
        # Initialize crawler
        crawler = CrawlerService(
            base_url=website.url,
            max_pages=preferences.get('max_pages', 100),
            max_depth=preferences.get('max_depth', 5),
        )
        
        # Crawl website (run async function in sync context)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        pages_data = loop.run_until_complete(crawler.crawl())
        loop.close()
        
        # Update statistics
        scan_session.pages_found = len(pages_data)
        db.commit()
        
        # Process each page
        total_errors = 0
        
        for page_data in pages_data:
            # Create page record
            page = Page(
                scan_session_id=scan_session.id,
                url=page_data['url'],
                title=page_data.get('title'),
                status_code=page_data.get('status_code'),
                html_content=page_data.get('html_content'),
                text_content=page_data.get('text_content'),
                meta_description=page_data.get('meta', {}).get('description'),
                meta_keywords=page_data.get('meta', {}).get('keywords'),
                has_favicon=page_data.get('meta', {}).get('has_favicon', False),
                depth=page_data.get('depth', 0),
            )
            db.add(page)
            db.flush()  # Get page.id
            
            # Run checks
            page_errors = []
            
            # 1. Spell checking
            if preferences.get('check_spelling', True) and page_data.get('text_content'):
                with SpellCheckerService() as spell_checker:
                    whitelist = preferences.get('whitelist_words', [])
                    spell_errors = spell_checker.check_page(
                        page_data['text_content'],
                        whitelist_words=whitelist
                    )
                    
                    for err in spell_errors:
                        error = Error(
                            page_id=page.id,
                            error_type=ErrorType.SPELLING,
                            severity=ErrorSeverity.WARNING,
                            message=err['message'],
                            context=err.get('context'),
                            suggestion=err.get('suggestion'),
                        )
                        page_errors.append(error)
            
            # 2. Address validation
            if preferences.get('check_addresses', True) and page_data.get('text_content'):
                address_validator = AddressValidatorService()
                address_errors = address_validator.validate_text(page_data['text_content'])
                
                for err in address_errors:
                    error = Error(
                        page_id=page.id,
                        error_type=ErrorType.ADDRESS,
                        severity=ErrorSeverity.ERROR,
                        message=err['message'],
                        context=err.get('context'),
                        suggestion=err.get('suggestion'),
                    )
                    page_errors.append(error)
            
            # 3. Link checking (async)
            if preferences.get('check_links', True) and page_data.get('html_content'):
                link_checker = LinkCheckerService()
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                link_errors = loop.run_until_complete(
                    link_checker.check_all_links(page_data['html_content'], page_data['url'])
                )
                loop.close()
                
                for err in link_errors:
                    error = Error(
                        page_id=page.id,
                        error_type=ErrorType.BROKEN_LINK,
                        severity=ErrorSeverity.ERROR,
                        message=err['message'],
                        link_url=err.get('link_url'),
                        link_status_code=err.get('status_code'),
                    )
                    page_errors.append(error)
            
            # 4. Phone number checking
            if preferences.get('check_phones', True) and page_data.get('html_content'):
                link_checker = LinkCheckerService()
                phone_errors = link_checker.check_phone_numbers(page_data['html_content'])
                
                for err in phone_errors:
                    error = Error(
                        page_id=page.id,
                        error_type=ErrorType.PHONE,
                        severity=ErrorSeverity.WARNING,
                        message=err['message'],
                        context=err.get('context'),
                        suggestion=err.get('suggestion'),
                    )
                    page_errors.append(error)
            
            # 5. SEO checking (async, only for first page / home page)
            if preferences.get('check_seo', True) and page_data.get('html_content'):
                seo_checker = SEOCheckerService()
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                seo_errors = loop.run_until_complete(
                    seo_checker.check_page(page_data['html_content'], page_data['url'])
                )
                
                # Check robots.txt (only once, for homepage)
                if page_data.get('depth', 0) == 0:
                    robots_error = loop.run_until_complete(
                        seo_checker.check_robots_accessibility(website.url)
                    )
                    if robots_error:
                        seo_errors.append(robots_error)
                
                loop.close()
                
                for err in seo_errors:
                    severity_map = {
                        'info': ErrorSeverity.INFO,
                        'warning': ErrorSeverity.WARNING,
                        'error': ErrorSeverity.ERROR,
                        'critical': ErrorSeverity.CRITICAL,
                    }
                    error = Error(
                        page_id=page.id,
                        error_type=ErrorType.SEO,
                        severity=severity_map.get(err.get('severity', 'warning'), ErrorSeverity.WARNING),
                        message=err['message'],
                        suggestion=err.get('suggestion'),
                    )
                    page_errors.append(error)
            
            # Save all errors
            for error in page_errors:
                db.add(error)
            
            total_errors += len(page_errors)
            
            # Update progress
            scan_session.pages_processed += 1
            scan_session.errors_found = total_errors
            db.commit()
            
            # Update task progress
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': scan_session.pages_processed,
                    'total': scan_session.pages_found,
                    'errors': total_errors,
                }
            )
        
        # Complete scan
        scan_session.status = ScanStatus.COMPLETED
        scan_session.completed_at = datetime.utcnow()
        db.commit()
        
        return {
            'status': 'completed',
            'pages_found': scan_session.pages_found,
            'pages_processed': scan_session.pages_processed,
            'errors_found': scan_session.errors_found,
        }
        
    except Exception as e:
        scan_session.status = ScanStatus.FAILED
        scan_session.error_message = str(e)
        scan_session.completed_at = datetime.utcnow()
        db.commit()
        raise
    finally:
        db.close()

