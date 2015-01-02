import traceback

from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from couchpotato.core.helpers.encoding import toUnicode
from couchpotato.core.helpers.variable import tryInt, getIdentifier
from couchpotato.core.logger import CPLog
from couchpotato.core.media._base.providers.torrent.base import TorrentProvider
import re

log = CPLog(__name__)


class Base(TorrentProvider):

    urls = {
        'login' : 'https://hd-space.org/index.php?page=login',
        'detail' : 'https://hd-space.org/index.php?page=torrent-details&id=%s',
        'search' : 'https://hd-space.org/index.php?page=torrents&search=%s&active=1&options=2',
        'home' : 'https://hd-space.org/%s',
    }

    http_time_between_calls = 1 #seconds

    def _search(self, movie, quality, results):
        imdbId = getIdentifier (movie).replace ("t", "")
        url = self.urls['search'] % (imdbId)#, cats[0])
        data = self.getHTMLData(url)
        
        if data:
          
          # Remove HDSpace NEW list
          split_data = data.partition('<form name="tcategories" action="index.php" method="post">')
          data = split_data[2]

          html = BeautifulSoup(data)
          try:
              #Now attempt to get any others
              result_table = html.find('table', attrs = {'class' : 'lista'})
              if not result_table:
                  return

              entries = result_table.find_all('tr')
              log.info("entries length: %s", len(entries))

              if not entries:
                  return

              for result in entries:
                  block2 = result.find_all('td', attrs={'class' : 'header'})
                  # Ignore header
                  if block2:
                      continue
                  cells = result.find_all('td')
                  log.info("cells length: %s", len(cells))

                  extend = 0
                  detail = cells[1 + extend].find('a')['href']
                  torrent_id = detail.replace('index.php?page=torrent-details&id=', '')
                  try:
                    torrent_age = datetime.now() - datetime.strptime(cells[4 + extend].get_text().encode('ascii','ignore'), '%B %d, %Y,%H:%M:%S')
                  except:
                    torrent_age = timedelta(1)

                  results.append({
                                  'id': torrent_id,
                                  'name': cells[9 + extend].find('a')['title'].strip('History - ').replace('Blu-ray', 'bd50'),
                                  'url': self.urls['home'] % cells[3 + extend].find('a')['href'],
                                  'detail_url': self.urls['home'] % cells[1 + extend].find('a')['href'],
                                  'size': self.parseSize(cells[5 + extend].get_text()),
                                  'age': torrent_age.days,
                                  'seeders': tryInt(cells[7 + extend].find('a').get_text()),
                                  'leechers': tryInt(cells[8 + extend].find('a').get_text()),
                                  'get_more_info': self.getMoreInfo,
                  })

          except:
              log.error('Failed getting results from %s: %s', (self.getName(), traceback.format_exc()))

    def getMoreInfo(self, item):
        full_description = self.getCache('hdspace.%s' % item['id'], item['detail_url'], cache_timeout = 25920000)
        html = BeautifulSoup(full_description)
        nfo_pre = html.find('div', attrs = {'id':'details_table'})
        description = toUnicode(nfo_pre.text) if nfo_pre else ''

        item['description'] = description
        return item

    def getLoginParams(self):
        return {
            'uid': self.conf('username'),
            'pwd': self.conf('password'),
            'Login': 'submit',
        }

    def loginSuccess(self, output):
        return "if your browser doesn\'t have javascript enabled" or 'logout.php' in output.lower()

    loginCheckSuccess = loginSuccess


config = [{
    'name': 'hdspace',
    'groups': [
        {
            'tab': 'searcher',
            'list': 'torrent_providers',
            'name': 'HDSpace',
            'description': 'See <a href="https://hd-space.org">HDSpace</a>',
            'wizard': True,
            'options': [
                {
                    'name': 'enabled',
                    'type': 'enabler',
                    'default': False,
                },
                {
                    'name': 'username',
                    'default': '',
                },
                {
                    'name': 'password',
                    'default': '',
                    'type': 'password',
                },
                {
                    'name': 'seed_ratio',
                    'label': 'Seed ratio',
                    'type': 'float',
                    'default': 1,
                    'description': 'Will not be (re)moved until this seed ratio is met.',
                },
                {
                    'name': 'seed_time',
                    'label': 'Seed time',
                    'type': 'int',
                    'default': 40,
                    'description': 'Will not be (re)moved until this seed time (in hours) is met.',
                },
                {
                    'name': 'extra_score',
                    'advanced': True,
                    'label': 'Extra Score',
                    'type': 'int',
                    'default': 20,
                    'description': 'Starting score for each release found via this provider.',
                }
            ],
        },
    ],
}]
