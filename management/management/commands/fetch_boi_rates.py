# management/management/commands/fetch_boi_rates.py
import datetime
import csv
from django.core.management.base import BaseCommand, CommandError
from management.models import CurrencyRate
from crm.models import Currency
from decimal import Decimal
import io

class Command(BaseCommand):
    help = 'Imports exchange rates from CSV files and saves them to CurrencyRate model.'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--file_path_usd',
            type=str,
            help='Path to the CSV file for USD/ILS rates.'
        )
        parser.add_argument(
            '--file_path_eur',
            type=str,
            help='Path to the CSV file for EUR/ILS rates.'
        )

    def handle(self, *args, **options):
        usd_file_path = options['file_path_usd']
        eur_file_path = options['file_path_eur']
        
        if not usd_file_path or not eur_file_path:
            raise CommandError("Both --file_path_usd and --file_path_eur arguments are required.")

        try:
            ils_currency_obj, _ = Currency.objects.get_or_create(code='ILS', defaults={'name': 'שקל חדש'})
        except Exception as e:
            raise CommandError(f"Error getting/creating ILS currency: {e}")

        # Dictionary to hold rates for a specific date
        daily_rates = {}

        # Process USD/ILS file
        self.process_file(usd_file_path, 'USD', ils_currency_obj, daily_rates)
        
        # Process EUR/ILS file
        self.process_file(eur_file_path, 'EUR', ils_currency_obj, daily_rates)

        # Calculate cross rates and save all to DB
        self.save_all_rates(daily_rates, ils_currency_obj)

        self.stdout.write(self.style.SUCCESS("All currency rates processed and saved successfully."))

    def process_file(self, file_path, from_code, to_currency_obj, daily_rates):
        """
        Reads a CSV file and stores the daily rates in a dictionary.
        """
        self.stdout.write(f"Processing file for {from_code}/{to_currency_obj.code} at {file_path}...")
        try:
            with io.open(file_path, 'r', encoding='utf-8-sig') as csvfile:
                reader = csv.reader(csvfile)
                next(reader)  # Skip header row
                
                from_currency_obj, _ = Currency.objects.get_or_create(code=from_code, defaults={'name': from_code})

                for row in reader:
                    if len(row) < 2:
                        continue
                        
                    rate_str, date_str = row
                    
                    try:
                        rate = Decimal(rate_str)
                        date = datetime.datetime.strptime(date_str.strip(), '%d/%m/%Y').date()
                        
                        if date not in daily_rates:
                            daily_rates[date] = {}
                        
                        # Store the rate for the pair
                        daily_rates[date][from_currency_obj] = rate
                        
                    except (ValueError, IndexError) as e:
                        self.stdout.write(self.style.WARNING(f"Skipping malformed row: {row}. Error: {e}"))
            
        except FileNotFoundError:
            raise CommandError(f"File not found at: {file_path}")
        except Exception as e:
            raise CommandError(f"Error processing CSV file: {e}")

    def save_all_rates(self, daily_rates, ils_currency_obj):
        """
        Calculates all permutations (USD/EUR, EUR/USD) and saves rates to the database.
        """
        usd_currency_obj = Currency.objects.get(code='USD')
        eur_currency_obj = Currency.objects.get(code='EUR')
        
        for date, rates in daily_rates.items():
            # Save USD/ILS
            if usd_currency_obj in rates:
                CurrencyRate.objects.update_or_create(
                    from_currency=usd_currency_obj, to_currency=ils_currency_obj, date=date,
                    defaults={'rate': rates[usd_currency_obj]}
                )
            
            # Save EUR/ILS
            if eur_currency_obj in rates:
                CurrencyRate.objects.update_or_create(
                    from_currency=eur_currency_obj, to_currency=ils_currency_obj, date=date,
                    defaults={'rate': rates[eur_currency_obj]}
                )
            
            # Calculate and save ILS/USD (reciprocal)
            if usd_currency_obj in rates:
                CurrencyRate.objects.update_or_create(
                    from_currency=ils_currency_obj, to_currency=usd_currency_obj, date=date,
                    defaults={'rate': Decimal('1.0') / rates[usd_currency_obj]}
                )
            
            # Calculate and save ILS/EUR (reciprocal)
            if eur_currency_obj in rates:
                CurrencyRate.objects.update_or_create(
                    from_currency=ils_currency_obj, to_currency=eur_currency_obj, date=date,
                    defaults={'rate': Decimal('1.0') / rates[eur_currency_obj]}
                )
            
            # Calculate and save EUR/USD (cross rate)
            if eur_currency_obj in rates and usd_currency_obj in rates:
                cross_rate_eur_usd = rates[eur_currency_obj] / rates[usd_currency_obj]
                CurrencyRate.objects.update_or_create(
                    from_currency=eur_currency_obj, to_currency=usd_currency_obj, date=date,
                    defaults={'rate': cross_rate_eur_usd}
                )

            # Calculate and save USD/EUR (cross rate)
            if usd_currency_obj in rates and eur_currency_obj in rates:
                cross_rate_usd_eur = rates[usd_currency_obj] / rates[eur_currency_obj]
                CurrencyRate.objects.update_or_create(
                    from_currency=usd_currency_obj, to_currency=eur_currency_obj, date=date,
                    defaults={'rate': cross_rate_usd_eur}
                )

