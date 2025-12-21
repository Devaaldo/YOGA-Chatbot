"""
Google Places Details API - Tourism Data Scraper
Fetches detailed data including price, opening hours, kecamatan, kabupaten
Using 2-step process: Text Search → Place Details
"""

import json
import time
import logging
import requests
import re
from typing import Dict, List, Optional
from pathlib import Path
import pandas as pd

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('places_api_scraper.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class PlacesDetailsScraper:
    """Scraper using Google Places API for detailed tourism data"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://maps.googleapis.com/maps/api/place"
        self.session = requests.Session()

    def search_place(self, place_name: str, location_hint: str = "Yogyakarta") -> Optional[str]:
        """
        Step 1: Search for place and get place_id
        Using Text Search API
        """
        endpoint = f"{self.base_url}/textsearch/json"

        # Construct query
        query = f"{place_name}, {location_hint}"

        params = {
            'query': query,
            'key': self.api_key,
            'language': 'id',
            'region': 'id'
        }

        try:
            logger.info(f"Searching for: {query}")
            response = self.session.get(endpoint, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            if data.get('status') == 'OK' and data.get('results'):
                place_id = data['results'][0].get('place_id')
                logger.info(f"✓ Found place_id: {place_id}")
                return place_id
            else:
                logger.warning(f"✗ Place not found. Status: {data.get('status')}")
                return None

        except Exception as e:
            logger.error(f"✗ Error searching place: {e}")
            return None

    def get_place_details(self, place_id: str) -> Optional[Dict]:
        """
        Step 2: Get detailed information using place_id
        Using Place Details API
        """
        endpoint = f"{self.base_url}/details/json"

        # Request specific fields
        fields = [
            'name',
            'formatted_address',
            'address_components',
            'geometry',
            'opening_hours',
            'price_level',
            'rating',
            'user_ratings_total',
            'formatted_phone_number',
            'website',
            'url',
            'types'
        ]

        params = {
            'place_id': place_id,
            'fields': ','.join(fields),
            'key': self.api_key,
            'language': 'id'
        }

        try:
            logger.info(f"Fetching details for place_id: {place_id}")
            response = self.session.get(endpoint, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            if data.get('status') == 'OK':
                result = data.get('result', {})
                logger.info(f"✓ Got details for: {result.get('name')}")
                return result
            else:
                logger.warning(f"✗ Failed to get details. Status: {data.get('status')}")
                return None

        except Exception as e:
            logger.error(f"✗ Error getting place details: {e}")
            return None

    def extract_kecamatan_kabupaten(self, address_components: List[Dict]) -> Dict[str, str]:
        """
        Extract kecamatan and kabupaten from address_components
        """
        info = {
            'kecamatan': None,
            'kabupaten': None,
            'provinsi': None
        }

        for component in address_components:
            types = component.get('types', [])
            long_name = component.get('long_name', '')

            # Kecamatan = sublocality_level_1 or administrative_area_level_3
            if 'sublocality_level_1' in types or 'administrative_area_level_3' in types:
                # Clean "Kecamatan" prefix if present
                kec = re.sub(r'^Kecamatan\s+', '', long_name, flags=re.IGNORECASE)
                info['kecamatan'] = kec

            # Kabupaten/Kota = administrative_area_level_2
            if 'administrative_area_level_2' in types:
                info['kabupaten'] = long_name

            # Provinsi = administrative_area_level_1
            if 'administrative_area_level_1' in types:
                info['provinsi'] = long_name

        return info

    def parse_opening_hours(self, opening_hours: Dict) -> str:
        """
        Parse opening_hours to readable format
        """
        if not opening_hours:
            return "N/A"

        # Get weekday_text (array of strings like "Monday: 9:00 AM – 5:00 PM")
        weekday_text = opening_hours.get('weekday_text', [])

        if weekday_text:
            # Join with semicolon for CSV compatibility
            return "; ".join(weekday_text)

        # Fallback: check if open_now
        open_now = opening_hours.get('open_now')
        if open_now is not None:
            return "Open 24 hours" if open_now else "Closed"

        return "N/A"

    def map_price_level(self, price_level: Optional[int]) -> str:
        """
        Map Google price_level (0-4) to Indonesian price range

        Google scale:
        0 = Free
        1 = Inexpensive (< Rp 50.000)
        2 = Moderate (Rp 50.000 - Rp 150.000)
        3 = Expensive (Rp 150.000 - Rp 300.000)
        4 = Very Expensive (> Rp 300.000)
        """
        if price_level is None:
            return "N/A"

        price_map = {
            0: "Gratis",
            1: "< Rp 50.000",
            2: "Rp 50.000 - Rp 150.000",
            3: "Rp 150.000 - Rp 300.000",
            4: "> Rp 300.000"
        }

        return price_map.get(price_level, "N/A")

    def scrape_place(self, place_name: str, location_hint: str = "Yogyakarta") -> Dict:
        """
        Complete scraping process for one place
        """
        result = {
            'place_name': place_name,
            'success': False,
            'data': {},
            'error': None
        }

        try:
            # Step 1: Search for place_id
            place_id = self.search_place(place_name, location_hint)

            if not place_id:
                result['error'] = "Place not found in search"
                return result

            # Small delay to avoid rate limiting
            time.sleep(0.5)

            # Step 2: Get place details
            details = self.get_place_details(place_id)

            if not details:
                result['error'] = "Failed to get place details"
                return result

            # Extract address info
            address_components = details.get('address_components', [])
            location_info = self.extract_kecamatan_kabupaten(address_components)

            # Extract opening hours
            opening_hours_raw = details.get('opening_hours', {})
            opening_hours_text = self.parse_opening_hours(opening_hours_raw)

            # Extract price
            price_level = details.get('price_level')
            price_text = self.map_price_level(price_level)

            # Compile data
            result['data'] = {
                'nama': details.get('name', place_name),
                'kecamatan': location_info.get('kecamatan'),
                'kabupaten': location_info.get('kabupaten'),
                'provinsi': location_info.get('provinsi'),
                'harga': price_text,
                'jam_buka': opening_hours_text,
                'rating': details.get('rating'),
                'reviews_count': details.get('user_ratings_total'),
                'phone': details.get('formatted_phone_number'),
                'website': details.get('website'),
                'address': details.get('formatted_address'),
                'google_maps_url': details.get('url'),
                'place_id': place_id,
                'types': ', '.join(details.get('types', []))
            }

            result['success'] = True

            logger.info(f"✓ Successfully scraped: {place_name}")
            logger.info(f"  Kecamatan: {location_info.get('kecamatan')}")
            logger.info(f"  Kabupaten: {location_info.get('kabupaten')}")
            logger.info(f"  Harga: {price_text}")
            logger.info(f"  Jam buka: {opening_hours_text[:50]}...")

        except Exception as e:
            logger.error(f"✗ Error scraping {place_name}: {e}")
            result['error'] = str(e)

        return result

    def parse_places_from_intents(self, intents_file: str) -> List[Dict[str, str]]:
        """
        Parse tourist places from intents_diy_full.json
        Extract Top 5 wisata from each kecamatan intent
        """
        logger.info(f"Parsing places from: {intents_file}")

        with open(intents_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        places = []
        intents_list = data.get('intents', [])

        for intent in intents_list:
            tag = intent.get('tag', '')

            # Only process kecamatan intents
            if not tag.startswith('kecamatan_'):
                continue

            # Extract kecamatan name from tag
            kecamatan_name = tag.replace('kecamatan_', '').replace('_', ' ').title()

            responses = intent.get('responses', [])

            # Find the response with Top 5 list
            for response in responses:
                if 'Top 5' in response or any(str(i) in response for i in range(1, 6)):
                    # Extract numbered items (1. Place Name, 2. Place Name, etc.)
                    lines = response.split('\n')

                    for line in lines:
                        # Match patterns like "1. Place Name" or "- Place Name"
                        match = re.match(r'^\s*[\d\-\*]+[\.\)]\s*(.+)', line)
                        if match:
                            place_name = match.group(1).strip()

                            # Clean up common suffixes
                            place_name = re.sub(r'\s*\([^)]*\)\s*$', '', place_name)

                            if place_name:
                                places.append({
                                    'name': place_name,
                                    'kecamatan': kecamatan_name,
                                    'location_hint': f"{kecamatan_name}, Yogyakarta"
                                })

                    break  # Found the Top 5 list, no need to check other responses

        logger.info(f"✓ Parsed {len(places)} places from {len([i for i in intents_list if i.get('tag', '').startswith('kecamatan_')])} kecamatan intents")

        return places

    def scrape_all_places(self, intents_file: str, output_csv: str, output_json: str):
        """
        Main scraping function - scrape all places and save to CSV/JSON
        """
        logger.info("="*70)
        logger.info("STARTING GOOGLE PLACES API SCRAPING")
        logger.info("="*70)

        # Parse places from intents
        places = self.parse_places_from_intents(intents_file)

        if not places:
            logger.error("✗ No places found in intents file!")
            return

        logger.info(f"Total places to scrape: {len(places)}")

        results = []

        for idx, place in enumerate(places, 1):
            logger.info(f"\n[{idx}/{len(places)}] Processing: {place['name']}")
            logger.info("-" * 70)

            result = self.scrape_place(place['name'], place['location_hint'])

            # Add source kecamatan
            if result['success']:
                result['data']['source_kecamatan'] = place['kecamatan']

            results.append(result)

            # Save intermediate results every 10 places
            if idx % 10 == 0:
                self._save_intermediate(results, output_json)
                logger.info(f"💾 Saved intermediate results ({idx} places)")

            # Rate limiting: wait between requests
            time.sleep(1)  # 1 second between places (avoid hitting rate limits)

        # Save final results
        self._save_results(results, output_csv, output_json)

        # Print summary
        self._print_summary(results)

    def _save_intermediate(self, results: List[Dict], json_file: str):
        """Save intermediate results to JSON"""
        intermediate_file = json_file.replace('.json', '_intermediate.json')

        with open(intermediate_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

    def _save_results(self, results: List[Dict], csv_file: str, json_file: str):
        """Save final results to CSV and JSON"""
        logger.info("\n" + "="*70)
        logger.info("SAVING RESULTS")
        logger.info("="*70)

        # Save JSON
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        logger.info(f"✓ Saved JSON: {json_file}")

        # Convert to DataFrame
        rows = []
        for result in results:
            if result['success']:
                row = {
                    'place_name': result['place_name'],
                    **result['data']
                }
            else:
                row = {
                    'place_name': result['place_name'],
                    'error': result.get('error', 'Unknown error'),
                    'success': False
                }

            rows.append(row)

        df = pd.DataFrame(rows)

        # Reorder columns
        column_order = [
            'place_name', 'nama', 'kecamatan', 'kabupaten', 'provinsi',
            'harga', 'jam_buka', 'rating', 'reviews_count',
            'phone', 'website', 'address', 'google_maps_url',
            'source_kecamatan', 'place_id', 'types'
        ]

        # Only use columns that exist
        existing_cols = [col for col in column_order if col in df.columns]
        df = df[existing_cols]

        # Save CSV
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')

        logger.info(f"✓ Saved CSV: {csv_file}")

    def _print_summary(self, results: List[Dict]):
        """Print scraping summary statistics"""
        logger.info("\n" + "="*70)
        logger.info("SCRAPING SUMMARY")
        logger.info("="*70)

        total = len(results)
        success = sum(1 for r in results if r['success'])
        failed = total - success

        logger.info(f"\n📊 Overall Statistics:")
        logger.info(f"  Total places: {total}")
        logger.info(f"  Success: {success} ({success/total*100:.1f}%)")
        logger.info(f"  Failed: {failed} ({failed/total*100:.1f}%)")

        # Data completeness
        successful_results = [r for r in results if r['success']]

        if successful_results:
            with_price = sum(1 for r in successful_results if r['data'].get('harga') and r['data']['harga'] != 'N/A')
            with_hours = sum(1 for r in successful_results if r['data'].get('jam_buka') and r['data']['jam_buka'] != 'N/A')
            with_rating = sum(1 for r in successful_results if r['data'].get('rating'))
            with_kec = sum(1 for r in successful_results if r['data'].get('kecamatan'))
            with_kab = sum(1 for r in successful_results if r['data'].get('kabupaten'))
            with_phone = sum(1 for r in successful_results if r['data'].get('phone'))
            with_website = sum(1 for r in successful_results if r['data'].get('website'))

            logger.info(f"\n📈 Data Completeness (out of {success} successful):")
            logger.info(f"  With price: {with_price} ({with_price/success*100:.1f}%)")
            logger.info(f"  With opening hours: {with_hours} ({with_hours/success*100:.1f}%)")
            logger.info(f"  With rating: {with_rating} ({with_rating/success*100:.1f}%)")
            logger.info(f"  With kecamatan: {with_kec} ({with_kec/success*100:.1f}%)")
            logger.info(f"  With kabupaten: {with_kab} ({with_kab/success*100:.1f}%)")
            logger.info(f"  With phone: {with_phone} ({with_phone/success*100:.1f}%)")
            logger.info(f"  With website: {with_website} ({with_website/success*100:.1f}%)")


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description='Scrape tourism data using Google Places API')
    parser.add_argument('--api-key', required=True, help='Google Places API key')
    parser.add_argument('--intents', default='../data/intents_diy_full.json', help='Path to intents JSON file')
    parser.add_argument('--output-csv', default='../data/tourism_places_details.csv', help='Output CSV file')
    parser.add_argument('--output-json', default='../data/tourism_places_details.json', help='Output JSON file')
    parser.add_argument('--max-places', type=int, help='Maximum number of places to scrape (for testing)')

    args = parser.parse_args()

    # Create scraper
    scraper = PlacesDetailsScraper(args.api_key)

    # Parse places
    places = scraper.parse_places_from_intents(args.intents)

    # Limit if testing
    if args.max_places:
        logger.info(f"⚠️ Testing mode: limiting to {args.max_places} places")
        places_subset = places[:args.max_places]

        # Manually scrape subset
        results = []
        for idx, place in enumerate(places_subset, 1):
            logger.info(f"\n[{idx}/{len(places_subset)}] Processing: {place['name']}")
            result = scraper.scrape_place(place['name'], place['location_hint'])
            if result['success']:
                result['data']['source_kecamatan'] = place['kecamatan']
            results.append(result)
            time.sleep(1)

        scraper._save_results(results, args.output_csv, args.output_json)
        scraper._print_summary(results)
    else:
        # Full scraping
        scraper.scrape_all_places(args.intents, args.output_csv, args.output_json)


if __name__ == '__main__':
    main()
