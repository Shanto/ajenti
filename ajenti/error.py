from ajenti.utils import *
from ajenti import version
from ajenti.ui import UI
from ajenti.ui.template import BasicTemplate
import platform


def format_error(app, err):
    print '\n%s\n' % err
    templ = app.get_template('error.xml')
    templ.appendChildInto('trace',
            UI.TextInputArea(value=err, width=350))
    templ.appendChildInto('report',
            UI.TextInputArea(value=make_report(app, err), width=350))
    return templ.render()

def format_backend_error(app, ex):
    templ = app.get_template('nobackend.xml')
    text = 'You need a plugin that provides <b>%s</b> interface support for <b>%s</b> platform.<br/>' % (ex.interface, ex.platform)
    templ.appendChildInto('hint', UI.CustomHTML(html=text))
    return templ.render()

def make_report(app, err):
    pr = ''
    for p in app.class_list():
        i = ''
        if hasattr(p, '_implements'):
            imps = []
            for imp in p._implements:
                try:
                    imps.append(imp[0])
                except:
                    imps.append(imp)
            i = ','.join([x.__name__ for x in imps])
        pr += '%s [%s]\n' % (p.__name__, i)

    return (('Ajenti %s bug report\n' +
           '--------------------\n\n' +
           'System: %s\n' +
           'Detected platform: %s\n' +
           'Detected distro: %s\n' +
           'Python: %s\n\n' +
           'Config path: %s\n\n' +
           'Config content:\n%s\n' +
           '\n\nLoaded plugins:\n%s\n\n' +
           '%s')
            % (version,
               shell('uname -a'),
               detect_platform(),
               detect_distro(),
               '.'.join([str(x) for x in platform.python_version_tuple()]),
               app.config.filename,
               open(app.config.filename).read(),
               pr,
               err
              ))
              

class BackendUnavailableException(Exception):
    def __init__(self, interface, platform):
        self.interface = interface
        self.platform = platform
                      
