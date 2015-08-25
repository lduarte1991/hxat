#AnnotationsX
Harvard ATG's port of the edX Annotation tool to the Canvas LMS platform, forked from [hx-annotations-lti](https://github.com/lduarte1991/hx-annotations-lti).

#Installation

1. Download the source code
`git clone https://github.com/Harvard-ATG/annotationsx`

2. Add a file named 'secure.py' to your settings directory. (See 'secure.py example' at the bottom)
`AnnotationsX/annotationsx/settings/secure.py`

3. Install requirements 
	`sudo pip install -r requirements.txt`
	
4. Setup postgres
	* OSX Installation
		* Download the postgres App [here](http://postgresapp.com/)
			* (We're using the app version and porting it to the command line, because it makes it very easy to stop & start Postgres, but if you want the command line version, setup is very similar to the Linux instructions below)
		* Execute the following command to modify your bash PATH so you can access the postgres command-line tools
			` echo "export PATH='/Applications/Postgres.app/Contents/Versions/9.4/bin:$PATH'" >> ~/.bash_profile `
		* You'll have to open a new terminal to reload the bash profile.
		* Make sure the Postgres App is running.
		* Create the annotationsx database and user, prompting for a password and granting DB creation purposes (for `./manage.py test`).
			`createdb annotationsx`
			`createuser --pwprompt --createdb annotationsx`
	* Linux installation
		* Start the postgres daemon
			`sudo service postgresql start`
		* Login as the postgres superuser
			`sudo su - postgres`
		* Create the annotationsx database and user, prompting for a password and granting DB creation purposes (so executing the test suite doesn't fail).
			`createdb annotationsx`
			`createuser --pwprompt --createdb annotationsx`

5. Setup the database
	`./manage.py migrate && ./manage.py syncdb`
	
6. Run the server
	`./manage.py runserver`

7. Go to [lti/config](http://localhost:8000/lti/config) and copy the XML that shows up

8. In your Canvas course, click
>Settings -> Apps -> View App Configurations -> Add App

	* Select 'Paste XML'
	* Paste XML
	* Name your App
	* Enter your key and secret
	* Save

9. The AnnotationX Tool will be in the sidebar of your course

10. **Party**

<br/>
Party Favor - secure.py example:
```
SECURE_SETTINGS = {
	'debug' : True,
	'https_only': False,
	'django_secret_key': 'secretKey',
	'lti_oauth_credentials' : {'key':'secret'},
	'db_default_name' : 'annotationsx',
	'db_default_user': 'annotationsx',
	'db_default_password' : 'password',
	'X_FRAME_ALLOWED_SITES': {
		'tlt.harvard.edu',
		'edx.org',
		'harvardx.harvard.edu'
	},
	'X_FRAME_ALLOWED_SITES_MAP': {
		'tlt.harvard.edu':'canvas.harvard.edu',
		'edx.org':'edx.org',
		'harvardx.harvard.edu':'harvardx.harvard.edu'
	},
	'ADMIN_ROLES': {
		'Administrator', 'Instructor', 'TeachingAssistant',
		'urn:lti:role:ims/lis/Administrator',
		'urn:lti:role:ims/lis/Instructor',
		'urn:lti:role:ims/lis/TeachingAssistant',
	},
	'annotation_database_url': 'https://something/catch/annotator',
	'annotation_db_api_key': 'fake90210-123',
	'annotation_db_secret_token': 'fake123-1231',

}
```

#Differences from hx-annotations-lti
Below is an overview of the differences between Harvard ATG's [fork](https://github.com/Harvard-ATG/annotationsx) and [hx-annotations-lti](https://github.com/lduarte1991/hx-annotations-lti):
### Major Changes
* Installation: The tool is now integrated with [django-app-lti](https://github.com/Harvard-ATG/django-app-lti), so setup is now via XML configuration. As a result, the tool is launched from the left hand nav of Canvas as opposed to a module. Note that the functionality of adding the tool as a module is still available if needed.
* Authentication: Students are routed to a modified version of `admin_hub` with restricted privileges as opposed to an assignment page upon application launch
* An instructor dashboard which enables instructors to view annotations by student 
* Ability to delete assignments
* Added sessions via cookies
* Commented out certain features that have not yet been implemented or are deprecated:
	* Edit Course Form
		* Add CSS default is commented out (not yet implemented)
		* The Course admins selector is commented out (deprecated)
	* Assignment Form
		* Under Annotator Settings, the Allow Highlights checkbox is automatically checked and hidden as a temporary fix to a bug which was preventing the display of annotations in the sidebar
	* The Add New Source Material button is commented out (deprecated), although the addition of new source material can still be accomplished from the Assignment Form
	* Setup Info dialog commented out (deprecated)

### Minor Changes
* Instructors have edit and delete privileges for the annotations of all users.
* The Instructor tab of the sidebar filters for the annotations of all users who are `course_admins` for an assignment. Note that this is different from `ADMIN_ROLES`(`secure.py`).
* Only displays the data for the course (`active_course`) on which the tool is installed, as opposed to all courses for the user
* Default course name: On creation, the course name is set to the `context_title` LTI launch parameter by default
* Default population of forms:
  * Assignment Form 
	  * The Course selector is set to the current course by default
		* Database Settings is pre-populated with values from `secure.py`
		*  Under Annotation Table settings, the Pagination limit is set to 20 by default 
	* Target Form
		* The Course selector is set to the current course by default
		* The Creator selector is set to the current user by default
* Home buttons on assignment pages
* Small UI/cosmetic changes
* Minor bug fixes

## Launch
The location/workflow of the tool within canvas has been altered for ATG/FAS.
Instead of creating a module, the tool is now located at the left navigation bar of its course.

![Left Nav](http://i.imgur.com/T3ko1kR.png)

In addition, instead of copying and pasting specific launch details into the Canvas App configuration, those details are now inferred from the code and context. 
To facilitate that, we had to give students an index view by routing them to a modified version of `admin_hub`, from which they can choose an assignment/object to annotate. Whether a user is directed to the fully-featured `admin_hub` or stripped down version is determined by whether the user has a role defined within `ADMIN_ROLES` (`secure.py`).

## Instructor Dashboard
The instructor dashboard enables anyone with a role defined in `ADMIN_ROLES` from `secure.py` (e.g. an Instructor or TF) to view annotations on a per-student basis. Given that the user has an admin role, the instructor dashboard can be accessed by clicking on the Instructor Dashboard button on the homepage of the tool. 

![Instructor Dashboard](http://i.imgur.com/LbxYAsq.png)

The instructor dashboard displays an alphabetically sorted list of members of the course who have launched the tool at least once. Clicking on the name of any user expands the panel to show a table of annotations that the user has made. Each table row includes the date, assignment name, target object, line, annotation text and tags for each annotation. Clicking on a link under the Object column will lead the user to the Target Object on which a given annotation was made.

An instructor can filter through the users of the course by entering search text in the Filter users box at the top of the page. The instructor can toggle whether to filter users by name or content. Content refers to any text contained within the panel body for a given user, so that includes date, assignment name target object, line, annotation text and tags. All searches automatically show and expand matching panels and are case insensitive.
