import os
import webapp2
import jinja2
from string import letters

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

class BlogHandler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        return render_str(template, **params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

# value of blog's parent
def blog_key(name = 'default'):
    return db.Key.from_path('blogs', name)

# posts that actually go into the database
class Post(db.Model):
       subject = db.StringProperty(required = True)
       content = db.TextProperty(required = True)
       created = db.DateTimeProperty(auto_now_add = True)
       last_modified = db.DateTimeProperty(auto_now = True)

       def render(self):
           self._render_text = self.content.replace('\n', '<br>')
           return render_str("post.html", p = self)

# handler for /blog
class BlogFront(BlogHandler):
    def get(self):
        posts = db.GqlQuery("SELECT * FROM Post ORDER BY created DESC LIMIT 10")
        self.render('front.html', posts = posts)

class PostPage(BlogHandler):
    def get(self, post_id):
        key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        post = db.get(key)

        if not post:
            self.error(404)
            return

        self.render("permalink.html", post = post)

class MainPage(BlogHandler):
    def render_front(self, title="", art="", error=""):
        arts = db.GqlQuery("SELECT * from Art ORDER BY created DESC")
        self.render("front.html", title=title, art=art, error=error, arts=arts)
            
class NewPost(BlogHandler):
    def get(self):
        self.render("newpost.html")

    def post(self):
        subject = self.request.get("subject")
        content = self.request.get("content")

        if subject and content:
            p = Post(parent = blog_key(), subject = subject, content = content)
            p.put()
            self.redirect('/blog/%s' % str(p.key().id()))
        else:
            error = "we need a subject and content please!"
            self.render("newpost.html", subject = subject, content = content, error = error)

app = webapp2.WSGIApplication([('/', MainPage),
                               ('/blog/?', BlogFront),
                               ('/blog/([0-9]+)', PostPage),
                               ('/blog/newPost', NewPost),
                                ],
                                debug=True)

