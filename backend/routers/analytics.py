"""
Analytics API Endpoints - Metrics, Insights, and Reporting
"""
from fastapi import APIRouter, HTTPException
from sqlalchemy import func, and_, or_
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

from ..database import SessionLocal, Lead, Company, Signal, Contact

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/overview", summary="Get analytics overview")
async def get_analytics_overview() -> Dict[str, Any]:
    """
    Get comprehensive analytics overview

    Returns key metrics across leads, companies, and signals
    """
    db = SessionLocal()
    try:
        # Lead metrics
        total_leads = db.query(Lead).count()
        hot_leads = db.query(Lead).filter(Lead.total_score >= 80).count()
        warm_leads = db.query(Lead).filter(
            and_(Lead.total_score >= 60, Lead.total_score < 80)
        ).count()
        nurture_leads = db.query(Lead).filter(
            and_(Lead.total_score >= 40, Lead.total_score < 60)
        ).count()

        # Score distribution
        avg_score = db.query(func.avg(Lead.total_score)).scalar() or 0

        # Status distribution
        status_dist = db.query(
            Lead.status,
            func.count(Lead.id)
        ).group_by(Lead.status).all()

        # Leads by bucket
        bucket_dist = db.query(
            Lead.score_bucket,
            func.count(Lead.id)
        ).group_by(Lead.score_bucket).all()

        # Company metrics
        total_companies = db.query(Company).count()
        companies_with_website = db.query(Company).filter(Company.website != None).count()
        companies_with_contacts = db.query(Company).filter(Company.contacts.any()).count()

        # Signal metrics
        total_signals = db.query(Signal).count()

        # Contact metrics
        total_contacts = db.query(Contact).count()
        total_emails = db.query(Contact).filter(Contact.email != None).count()
        total_phones = db.query(Contact).filter(Contact.phone != None).count()

        # Recent activity (last 7 days)
        week_ago = datetime.now() - timedelta(days=7)
        leads_this_week = db.query(Lead).filter(Lead.created_at >= week_ago).count()
        companies_this_week = db.query(Company).filter(Company.created_at >= week_ago).count()

        # Conversion potential
        leads_ready_to_contact = db.query(Lead).filter(
            and_(Lead.total_score >= 60, Lead.status == 'new')
        ).count()

        return {
            "leads": {
                "total": total_leads,
                "hot": hot_leads,
                "warm": warm_leads,
                "nurture": nurture_leads,
                "average_score": round(avg_score, 2),
                "by_status": {status: count for status, count in status_dist},
                "by_bucket": {bucket: count for bucket, count in bucket_dist},
                "this_week": leads_this_week,
                "ready_to_contact": leads_ready_to_contact
            },
            "companies": {
                "total": total_companies,
                "with_website": companies_with_website,
                "with_contacts": companies_with_contacts,
                "contact_rate": round(companies_with_contacts / total_companies * 100, 1) if total_companies > 0 else 0,
                "this_week": companies_this_week
            },
            "signals": {
                "total": total_signals,
                "per_company": round(total_signals / total_companies, 1) if total_companies > 0 else 0
            },
            "contacts": {
                "total": total_contacts,
                "emails": total_emails,
                "phones": total_phones
            },
            "insights": {
                "hot_lead_percentage": round(hot_leads / total_leads * 100, 1) if total_leads > 0 else 0,
                "average_score": round(avg_score, 2),
                "weekly_velocity": leads_this_week
            }
        }

    except Exception as e:
        logger.error(f"Error getting analytics overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/trends", summary="Get trend data")
async def get_trends(days: Optional[int] = 30) -> Dict[str, Any]:
    """
    Get trend data over time

    Shows lead creation velocity, score trends, and conversion metrics
    """
    db = SessionLocal()
    try:
        # Get leads for the specified period
        start_date = datetime.now() - timedelta(days=days)

        # Daily lead creation
        daily_leads = []
        for i in range(days):
            day = start_date + timedelta(days=i)
            next_day = day + timedelta(days=1)

            count = db.query(Lead).filter(
                and_(Lead.created_at >= day, Lead.created_at < next_day)
            ).count()

            daily_leads.append({
                "date": day.strftime("%Y-%m-%d"),
                "count": count
            })

        # Score trend (average score over time)
        score_trend = []
        for i in range(days):
            day = start_date + timedelta(days=i)
            next_day = day + timedelta(days=1)

            avg = db.query(func.avg(Lead.total_score)).filter(
                and_(Lead.created_at >= day, Lead.created_at < next_day)
            ).scalar() or 0

            score_trend.append({
                "date": day.strftime("%Y-%m-%d"),
                "average_score": round(avg, 2)
            })

        # Hot lead trend
        hot_trend = []
        for i in range(days):
            day = start_date + timedelta(days=i)
            next_day = day + timedelta(days=1)

            count = db.query(Lead).filter(
                and_(
                    Lead.created_at >= day,
                    Lead.created_at < next_day,
                    Lead.total_score >= 80
                )
            ).count()

            hot_trend.append({
                "date": day.strftime("%Y-%m-%d"),
                "hot_leads": count
            })

        return {
            "period_days": days,
            "daily_leads": daily_leads,
            "score_trend": score_trend,
            "hot_lead_trend": hot_trend
        }

    except Exception as e:
        logger.error(f"Error getting trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/top-companies", summary="Get top companies by score")
async def get_top_companies(limit: Optional[int] = 20) -> Dict[str, Any]:
    """
    Get top companies ranked by lead score

    Useful for identifying highest-priority targets
    """
    db = SessionLocal()
    try:
        # Get top companies
        top_companies = db.query(
            Company.name,
            Company.website,
            func.max(Lead.total_score).label('max_score'),
            func.avg(Lead.total_score).label('avg_score'),
            func.count(Lead.id).label('lead_count')
        ).join(Lead).group_by(Company.id).order_by(
            func.max(Lead.total_score).desc()
        ).limit(limit).all()

        companies_list = []
        for company in top_companies:
            companies_list.append({
                "company_name": company.name,
                "website": company.website,
                "max_score": round(company.max_score, 2) if company.max_score else 0,
                "avg_score": round(company.avg_score, 2) if company.avg_score else 0,
                "lead_count": company.lead_count
            })

        return {
            "total": len(companies_list),
            "companies": companies_list
        }

    except Exception as e:
        logger.error(f"Error getting top companies: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/pain-analysis", summary="Analyze pain tags")
async def analyze_pain_tags() -> Dict[str, Any]:
    """
    Analyze most common pain tags across leads

    Helps identify market trends and pain points
    """
    db = SessionLocal()
    try:
        # Get all leads with pain tags
        leads = db.query(Lead).filter(Lead.pain_tags != None).all()

        # Count pain tags
        pain_counts = {}
        for lead in leads:
            if lead.pain_tags:
                for tag in lead.pain_tags:
                    pain_counts[tag] = pain_counts.get(tag, 0) + 1

        # Sort by frequency
        sorted_pains = sorted(
            pain_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return {
            "total_unique_pains": len(pain_counts),
            "top_pains": [
                {"pain": pain, "count": count}
                for pain, count in sorted_pains[:20]
            ]
        }

    except Exception as e:
        logger.error(f"Error analyzing pain tags: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/conversion-funnel", summary="Get conversion funnel metrics")
async def get_conversion_funnel() -> Dict[str, Any]:
    """
    Get lead conversion funnel metrics

    Shows how leads progress through the sales pipeline
    """
    db = SessionLocal()
    try:
        # Count by status
        status_counts = {
            "new": 0,
            "contacted": 0,
            "qualified": 0,
            "pitched": 0,
            "trial": 0,
            "won": 0,
            "lost": 0,
            "parked": 0
        }

        results = db.query(
            Lead.status,
            func.count(Lead.id)
        ).group_by(Lead.status).all()

        for status, count in results:
            if status in status_counts:
                status_counts[status] = count

        # Calculate conversion rates
        total = sum(status_counts.values())
        contacted = status_counts["contacted"] + status_counts["qualified"] + \
                    status_counts["pitched"] + status_counts["trial"] + \
                    status_counts["won"]

        qualified = status_counts["qualified"] + status_counts["pitched"] + \
                    status_counts["trial"] + status_counts["won"]

        pitched = status_counts["pitched"] + status_counts["trial"] + status_counts["won"]
        trial = status_counts["trial"] + status_counts["won"]
        won = status_counts["won"]

        return {
            "funnel_stages": status_counts,
            "conversion_rates": {
                "new_to_contacted": round(contacted / total * 100, 1) if total > 0 else 0,
                "contacted_to_qualified": round(qualified / contacted * 100, 1) if contacted > 0 else 0,
                "qualified_to_pitched": round(pitched / qualified * 100, 1) if qualified > 0 else 0,
                "pitched_to_trial": round(trial / pitched * 100, 1) if pitched > 0 else 0,
                "trial_to_won": round(won / trial * 100, 1) if trial > 0 else 0,
                "overall_win_rate": round(won / total * 100, 1) if total > 0 else 0
            },
            "total_leads": total
        }

    except Exception as e:
        logger.error(f"Error getting conversion funnel: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/source-analysis", summary="Analyze lead sources")
async def analyze_sources() -> Dict[str, Any]:
    """
    Analyze lead sources and their effectiveness

    Shows which scraping sources produce the best leads
    """
    db = SessionLocal()
    try:
        # Get all signals with sources
        signals = db.query(
            Signal.source_type,
            func.count(Signal.id).label('count'),
            func.avg(Lead.total_score).label('avg_score')
        ).join(Lead).group_by(Signal.source_type).all()

        source_stats = []
        for signal in signals:
            source_stats.append({
                "source": signal.source_type,
                "signal_count": signal.count,
                "average_score": round(signal.avg_score, 2) if signal.avg_score else 0
            })

        # Sort by average score
        source_stats.sort(key=lambda x: x["average_score"], reverse=True)

        return {
            "total_sources": len(source_stats),
            "sources": source_stats
        }

    except Exception as e:
        logger.error(f"Error analyzing sources: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/recommendations", summary="Get actionable recommendations")
async def get_recommendations() -> Dict[str, Any]:
    """
    Get AI-powered recommendations for improving lead generation

    Analyzes patterns and suggests actions
    """
    db = SessionLocal()
    try:
        recommendations = []

        # Check for hot leads without contact
        hot_no_contact = db.query(Lead).filter(
            and_(
                Lead.total_score >= 80,
                Lead.status == 'new',
                ~Lead.company.has(Company.contacts.any())
            )
        ).count()

        if hot_no_contact > 0:
            recommendations.append({
                "priority": "high",
                "category": "action_required",
                "title": f"{hot_no_contact} hot leads without contact info",
                "action": "Run enrichment to find emails/phones for these leads",
                "impact": "Could unlock immediate sales opportunities"
            })

        # Check for stale leads
        week_ago = datetime.now() - timedelta(days=7)
        stale_leads = db.query(Lead).filter(
            and_(
                Lead.total_score >= 60,
                Lead.status == 'new',
                Lead.created_at < week_ago
            )
        ).count()

        if stale_leads > 0:
            recommendations.append({
                "priority": "medium",
                "category": "follow_up",
                "title": f"{stale_leads} warm leads created over a week ago",
                "action": "Follow up with these leads before they go cold",
                "impact": "Improve conversion rates"
            })

        # Check enrichment completion
        companies_without_website = db.query(Company).filter(Company.website == None).count()

        if companies_without_website > 10:
            recommendations.append({
                "priority": "low",
                "category": "data_quality",
                "title": f"{companies_without_website} companies missing website",
                "action": "Add website URLs to enable enrichment",
                "impact": "Better lead intelligence"
            })

        # Check for automated scraping
        total_leads = db.query(Lead).count()
        if total_leads < 50:
            recommendations.append({
                "priority": "high",
                "category": "growth",
                "title": "Low lead count - under 50 total leads",
                "action": "Set up automated job scraping to build pipeline",
                "impact": "Increase lead volume"
            })

        return {
            "total_recommendations": len(recommendations),
            "recommendations": recommendations
        }

    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
