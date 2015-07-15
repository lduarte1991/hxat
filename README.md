# Annotation for LTI
Contains the currently-in-development project by HarvardX
to bring the annotation tool currently living in the edX
platform to a more accessible LTI implementation. 

Info for Setup: https://wiki.harvard.edu/confluence/pages/viewpage.action?title=Documentation&spaceKey=atg

TODO: Rest of ReadMe

## Local Install (up to wiki instructions):

1: Clone the repo
```
  git clone https://github.com/Harvard-ATG/hx-annotations-lti.git
```

2: Make a virtual environment (and activate it)
```
  virtualenv ./env
  source ./env/bin/activate
```

3: Install requirements (TODO: update this for TLT structure)
```
  pip install -r requirements.txt
  pip install -r TODO/requirements/local.txt
```
  
4: Create the pg database and user

  -- (If on linux, execute: ```sudo su - postgres```  before running the following commands)

```
    createdb hx_annotations_lti
    createuser --pwprompt hx_annotations_lti
```

5: Misc. Setup (TODO: make sure manage.py is in project root dir - TLT structure)
```
  ./manage.py collectstatic
  ./manage.py syncdb
```

6: Party
```
  ./manage.py runserver
```

**(At this point, you'll have to go to the wiki to set up on canvas)**

## Troubleshooting
If you run into issues getting into the admin site, try running ```python manage.py migrate auth``` and then ```python manage.py migrate```
