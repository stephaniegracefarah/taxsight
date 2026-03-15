with source as (
    select * from {{ ref('platform_reporting') }}
),

staged as (
    select
        -- Primary key
        obligation_id,

        -- Geography
        country_iso3,
        country_name,

        -- Regime classification
        regime_type,
        regime_framework,

        -- Enactment status
        cast(is_enacted as boolean)                     as is_enacted,
        cast(effective_date as date)                    as effective_date,

        -- Platform applicability
        cast(applies_to_platform as boolean)            as applies_to_platform,
        cast(has_revenue_threshold as boolean)          as has_revenue_threshold,

        -- Obligations detail
        reporting_deadline,
        covered_activities,
        seller_transaction_threshold,
        seller_revenue_threshold,
        cast(single_registration_eligible as boolean)   as single_registration_eligible,

        -- Penalty fields
        penalty_financial_severity,
        penalty_operational_severity,
        penalties_description,

        -- Scoring inputs
        guidance_maturity,
        regulatory_attention_level,
        cast(complexity_score_base as integer)          as complexity_score_base,

        -- Data quality fields
        source_url,
        verbatim_quote,
        confidence_flag,
        cast(last_verified_date as date)                as last_verified_date,
        notes,

        -- Audit field
        current_timestamp                               as _loaded_at

    from source
)

select * from staged