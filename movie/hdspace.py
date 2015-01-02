from couchpotato.core.helpers.encoding import tryUrlencode
from couchpotato.core.event import fireEvent
from couchpotato.core.logger import CPLog
from couchpotato.core.media._base.providers.torrent.hdspace import Base
from couchpotato.core.media.movie.providers.base import MovieProvider

log = CPLog(__name__)

autoload = 'HDSpace'


class HDSpace(MovieProvider, Base):
    pass
