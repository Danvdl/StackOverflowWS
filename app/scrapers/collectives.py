import logging
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BASE_URL = "https://stackoverflow.com"


def scrape_collectives():
    """Scrape collectives from Stack Overflow."""
    collectives_url = f"{BASE_URL}/collectives-all"
    response = requests.get(collectives_url)
    
    if response.status_code != 200:
        logger.debug(f"Failed to retrieve data from {collectives_url}. Status code: {response.status_code}")
        return None
    
    soup = BeautifulSoup(response.text, 'html.parser')
    collectives = []

    collective_items = soup.find_all('div', class_='s-card')

    for item in collective_items:
        name_tag = item.find('h1', class_='fs-body2 mb0 fc-blue-500')
        name = name_tag.text.strip() if name_tag else "No name found"
        
        link_tag = item.find('a', class_='js-gps-track')
        link = link_tag['href'] if link_tag else "No link found"
        
        slug = link.split('/')[-1] if link else "No slug found"
        
        description_tag = item.find('span', class_='fs-body1 v-truncate2 ow-break-word')
        description = description_tag.text.strip() if description_tag else "No description found"
        logger.debug(f"Description: {description}")
        
        tags_url = f"{BASE_URL}{link}?tab=tags"
        tags = scrape_collective_tags(tags_url)

        external_links_url = f"{BASE_URL}{link}"
        external_links = scrape_collective_external_links(external_links_url)
        
        collective_dict = {
            'tags': tags,
            'external_links': external_links,
            'description': description,
            'link': link,
            'name': name,
            'slug': slug
        }
        collectives.append(collective_dict)

    return collectives


def scrape_collective_tags(tags_url):
    """Scrape tags from a collective's page."""
    tags = []
    page_number = 1

    while True:
        paginated_url = f"{tags_url}&page={page_number}"
        response = requests.get(paginated_url)
        
        if response.status_code != 200:
            logger.debug(f"Failed to retrieve tags from {paginated_url}. Status code: {response.status_code}")
            break
        
        soup = BeautifulSoup(response.text, 'html.parser')
        new_tags = [tag.text.strip() for tag in soup.find_all('a', class_='s-tag')]

        if not new_tags:
            break

        tags.extend(new_tags)
        page_number += 1

    return tags


def scrape_collective_external_links(external_links_url):
    """Scrape external links from a collective's page."""
    response = requests.get(external_links_url)
    
    if response.status_code != 200:
        logger.debug(f"Failed to retrieve external links from {external_links_url}. Status code: {response.status_code}")
        return []
    
    soup = BeautifulSoup(response.text, 'html.parser')
    external_links = []

    link_tags = soup.find_all('a', class_='s-link', target='_blank')
    
    for link_tag in link_tags:
        href = link_tag['href']
        link_type = link_tag.text.strip().lower()
        external_links.append({"type": link_type, "link": href})
    
    return external_links
