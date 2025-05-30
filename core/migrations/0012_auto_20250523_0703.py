# Generated by Django 5.2.1 on 2025-05-23 07:03

import django_db_views.migration_functions
import django_db_views.operations
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0011_possibleduplicatecontactrelationship_and_more"),
    ]

    operations = [
        django_db_views.operations.ViewRunPython(
            code=django_db_views.migration_functions.ForwardViewMigration(
                "SELECT \n                array_to_string(\n                    array_agg(duplicate_value ORDER BY duplicate_value), ','\n                ) AS id,  \n                array_agg(\n                    duplicate_value ORDER BY duplicate_value\n                ) AS duplicate_values,  \n                array_agg(\n                    duplicate_type ORDER BY duplicate_type\n                ) AS duplicate_fields,  \n                contact_ids,\n                EXISTS(\n                    SELECT 1 FROM core_dismissedduplicatecontact as dd\n                    WHERE dd.contact_ids = duplicate_groups.contact_ids\n                ) AS is_dismissed\n            FROM (\n            SELECT 'Name'                         AS duplicate_type, \n                   concat('Name: ', concat(TRIM(LOWER(first_name)), ' ', TRIM(LOWER(last_name))))    AS duplicate_value,\n                   array_agg(id ORDER BY id)::int[]         AS contact_ids\n            FROM core_contact\n            GROUP BY duplicate_value\n            HAVING count(1) > 1\n         UNION ALL \n            SELECT 'Email'                         AS duplicate_type, \n                   concat('Email: ', TRIM(LOWER(unnest(emails))))    AS duplicate_value,\n                   array_agg(id ORDER BY id)::int[]         AS contact_ids\n            FROM core_contact\n            GROUP BY duplicate_value\n            HAVING count(1) > 1\n        ) AS duplicate_groups\n            GROUP BY contact_ids\n            ORDER BY id, contact_ids",
                "core_possibleduplicatecontact",
                engine="django.db.backends.postgresql",
            ),
            reverse_code=django_db_views.migration_functions.BackwardViewMigration(
                "SELECT \n                row_number() over ()    AS id,\n                unnest(contact_ids)     AS contact_id,  \n                subq.id                 AS duplicate_values_id\n            FROM (\n            SELECT \n                array_to_string(\n                    array_agg(duplicate_value ORDER BY duplicate_value), ','\n                ) AS id,  \n                array_agg(\n                    duplicate_value ORDER BY duplicate_value\n                ) AS duplicate_values,  \n                array_agg(\n                    duplicate_type ORDER BY duplicate_type\n                ) AS duplicate_fields,  \n                contact_ids,\n                EXISTS(\n                    SELECT 1 FROM core_dismissedduplicate as dd\n                    WHERE dd.contact_ids = duplicate_groups.contact_ids\n                ) AS is_dismissed\n            FROM (\n            SELECT 'Name'                         AS duplicate_type, \n                   concat('Name: ', concat(TRIM(LOWER(first_name)), ' ', TRIM(LOWER(last_name))))    AS duplicate_value,\n                   array_agg(id ORDER BY id)::int[]         AS contact_ids\n            FROM core_contact\n            GROUP BY duplicate_value\n            HAVING count(1) > 1\n         UNION ALL \n            SELECT 'Email'                         AS duplicate_type, \n                   concat('Email: ', TRIM(LOWER(unnest(emails))))    AS duplicate_value,\n                   array_agg(id ORDER BY id)::int[]         AS contact_ids\n            FROM core_contact\n            GROUP BY duplicate_value\n            HAVING count(1) > 1\n         UNION ALL \n            SELECT 'Email Cc'                         AS duplicate_type, \n                   concat('Email Cc: ', TRIM(LOWER(unnest(email_ccs))))    AS duplicate_value,\n                   array_agg(id ORDER BY id)::int[]         AS contact_ids\n            FROM core_contact\n            GROUP BY duplicate_value\n            HAVING count(1) > 1\n        ) AS duplicate_groups\n            GROUP BY contact_ids\n            ORDER BY id, contact_ids\n        ) AS subq",
                "core_possibleduplicatecontact",
                engine="django.db.backends.postgresql",
            ),
            atomic=False,
        ),
        django_db_views.operations.ViewRunPython(
            code=django_db_views.migration_functions.ForwardViewMigration(
                "SELECT \n                row_number() over ()    AS id,\n                unnest(contact_ids)     AS contact_id,  \n                subq.id                 AS duplicate_values_id\n            FROM (\n            SELECT \n                array_to_string(\n                    array_agg(duplicate_value ORDER BY duplicate_value), ','\n                ) AS id,  \n                array_agg(\n                    duplicate_value ORDER BY duplicate_value\n                ) AS duplicate_values,  \n                array_agg(\n                    duplicate_type ORDER BY duplicate_type\n                ) AS duplicate_fields,  \n                contact_ids,\n                EXISTS(\n                    SELECT 1 FROM core_dismissedduplicatecontact as dd\n                    WHERE dd.contact_ids = duplicate_groups.contact_ids\n                ) AS is_dismissed\n            FROM (\n            SELECT 'Name'                         AS duplicate_type, \n                   concat('Name: ', concat(TRIM(LOWER(first_name)), ' ', TRIM(LOWER(last_name))))    AS duplicate_value,\n                   array_agg(id ORDER BY id)::int[]         AS contact_ids\n            FROM core_contact\n            GROUP BY duplicate_value\n            HAVING count(1) > 1\n         UNION ALL \n            SELECT 'Email'                         AS duplicate_type, \n                   concat('Email: ', TRIM(LOWER(unnest(emails))))    AS duplicate_value,\n                   array_agg(id ORDER BY id)::int[]         AS contact_ids\n            FROM core_contact\n            GROUP BY duplicate_value\n            HAVING count(1) > 1\n        ) AS duplicate_groups\n            GROUP BY contact_ids\n            ORDER BY id, contact_ids\n        ) AS subq",
                "core_possibleduplicatecontactrelationship",
                engine="django.db.backends.postgresql",
            ),
            reverse_code=django_db_views.migration_functions.BackwardViewMigration(
                "",
                "core_possibleduplicatecontactrelationship",
                engine="django.db.backends.postgresql",
            ),
            atomic=False,
        ),
        django_db_views.operations.ViewRunPython(
            code=django_db_views.migration_functions.ForwardViewMigration(
                "SELECT \n                array_to_string(\n                    array_agg(duplicate_value ORDER BY duplicate_value), ','\n                ) AS id,  \n                array_agg(\n                    duplicate_value ORDER BY duplicate_value\n                ) AS duplicate_values,  \n                array_agg(\n                    duplicate_type ORDER BY duplicate_type\n                ) AS duplicate_fields,  \n                organization_ids,\n                EXISTS(\n                    SELECT 1 FROM core_dismissedduplicateorganization as dd\n                    WHERE dd.organization_ids = duplicate_groups.organization_ids\n                ) AS is_dismissed\n            FROM (\n            SELECT 'Name and government'                         AS duplicate_type, \n                   concat('Name and government: ', concat(TRIM(LOWER(organization.name)), ', ', TRIM(LOWER(government.name))))    AS duplicate_value,\n                   array_agg(id ORDER BY id)::int[]         AS organization_ids\n            FROM core_organization organization \n            LEFT JOIN public.core_country government \n                ON organization.government_id = government.code\n            LEFT JOIN public.core_country country \n                ON organization.country_id = country.code    \n            GROUP BY duplicate_value\n            HAVING count(1) > 1\n        ) AS duplicate_groups\n            GROUP BY organization_ids\n            ORDER BY id, organization_ids",
                "core_possibleduplicateorganization",
                engine="django.db.backends.postgresql",
            ),
            reverse_code=django_db_views.migration_functions.BackwardViewMigration(
                "",
                "core_possibleduplicateorganization",
                engine="django.db.backends.postgresql",
            ),
            atomic=False,
        ),
        django_db_views.operations.ViewRunPython(
            code=django_db_views.migration_functions.ForwardViewMigration(
                "SELECT \n                row_number() over ()        AS id,\n                unnest(organization_ids)    AS organization_id,  \n                subq.id                     AS duplicate_values_id\n            FROM (\n            SELECT \n                array_to_string(\n                    array_agg(duplicate_value ORDER BY duplicate_value), ','\n                ) AS id,  \n                array_agg(\n                    duplicate_value ORDER BY duplicate_value\n                ) AS duplicate_values,  \n                array_agg(\n                    duplicate_type ORDER BY duplicate_type\n                ) AS duplicate_fields,  \n                organization_ids,\n                EXISTS(\n                    SELECT 1 FROM core_dismissedduplicateorganization as dd\n                    WHERE dd.organization_ids = duplicate_groups.organization_ids\n                ) AS is_dismissed\n            FROM (\n            SELECT 'Name and government'                         AS duplicate_type, \n                   concat('Name and government: ', concat(TRIM(LOWER(organization.name)), ', ', TRIM(LOWER(government.name))))    AS duplicate_value,\n                   array_agg(id ORDER BY id)::int[]         AS organization_ids\n            FROM core_organization organization \n            LEFT JOIN public.core_country government \n                ON organization.government_id = government.code\n            LEFT JOIN public.core_country country \n                ON organization.country_id = country.code    \n            GROUP BY duplicate_value\n            HAVING count(1) > 1\n        ) AS duplicate_groups\n            GROUP BY organization_ids\n            ORDER BY id, organization_ids\n        ) AS subq",
                "core_possibleduplicateorganizationrelationship",
                engine="django.db.backends.postgresql",
            ),
            reverse_code=django_db_views.migration_functions.BackwardViewMigration(
                "",
                "core_possibleduplicateorganizationrelationship",
                engine="django.db.backends.postgresql",
            ),
            atomic=False,
        ),
        django_db_views.operations.ViewDropRunPython(
            code=django_db_views.migration_functions.DropView(
                "core_possibleduplicate", engine="django.db.backends.postgresql"
            ),
            reverse_code=django_db_views.migration_functions.BackwardViewMigration(
                "SELECT \n                array_to_string(\n                    array_agg(duplicate_value ORDER BY duplicate_value), ','\n                ) AS id,  \n                array_agg(\n                    duplicate_value ORDER BY duplicate_value\n                ) AS duplicate_values,  \n                array_agg(\n                    duplicate_type ORDER BY duplicate_type\n                ) AS duplicate_fields,  \n                contact_ids,\n                EXISTS(\n                    SELECT 1 FROM core_dismissedduplicate as dd\n                    WHERE dd.contact_ids = duplicate_groups.contact_ids\n                ) AS is_dismissed\n            FROM (\n            SELECT 'Name'                         AS duplicate_type, \n                   concat('Name: ', concat(TRIM(LOWER(first_name)), ' ', TRIM(LOWER(last_name))))    AS duplicate_value,\n                   array_agg(id ORDER BY id)::int[]         AS contact_ids\n            FROM core_contact\n            GROUP BY duplicate_value\n            HAVING count(1) > 1\n         UNION ALL \n            SELECT 'Email'                         AS duplicate_type, \n                   concat('Email: ', TRIM(LOWER(unnest(emails))))    AS duplicate_value,\n                   array_agg(id ORDER BY id)::int[]         AS contact_ids\n            FROM core_contact\n            GROUP BY duplicate_value\n            HAVING count(1) > 1\n         UNION ALL \n            SELECT 'Email Cc'                         AS duplicate_type, \n                   concat('Email Cc: ', TRIM(LOWER(unnest(email_ccs))))    AS duplicate_value,\n                   array_agg(id ORDER BY id)::int[]         AS contact_ids\n            FROM core_contact\n            GROUP BY duplicate_value\n            HAVING count(1) > 1\n        ) AS duplicate_groups\n            GROUP BY contact_ids\n            ORDER BY id, contact_ids",
                "core_possibleduplicate",
                engine="django.db.backends.postgresql",
            ),
            atomic=False,
        ),
    ]
