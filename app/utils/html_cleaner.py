import re
from bs4 import BeautifulSoup


def clean_question_body(body_html, closed_reason=None, closed_date=None):
    """
    Clean and format the HTML body of a question to make it more readable.
    Preserves code blocks and important formatting.
    Removes 'Closed' notices and related messages.
    """
    soup = BeautifulSoup(body_html, 'html.parser')

    # Remove unnecessary tags but keep the content
    for tag in soup(['script', 'style', 'meta', 'link']):
        tag.decompose()

    closed_notice = soup.find('aside', class_='s-notice s-notice__info post-notice js-post-notice mb16')
    if closed_notice:
        closed_notice.decompose()

    if closed_reason:
        for elem in soup(text=lambda text: closed_reason in text):
            elem.extract()

    for elem in soup(text=re.compile(r'Closed\s*')):
        elem.extract()

    for elem in soup(text=re.compile(r'Closed \d+ hours ago')):
        elem.extract()

    for code_block in soup.find_all('pre'):
        code_block.insert_before('\n```')
        code_block.insert_after('```\n')

    for inline_code in soup.find_all('code'):
        inline_code.insert_before('`')
        inline_code.insert_after('`')

    for br in soup.find_all('br'):
        br.replace_with('\n')

    cleaned_text = soup.get_text(separator='\n').strip()
    return cleaned_text
