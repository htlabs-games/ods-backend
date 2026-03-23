# ods-backend
Main HTTP backend and API for ODYSEA's online services and website.

## Provides:
- User management (account creation, logging in, profile config, etc.)
- Level upload handling
- Level metadata fetching
- Messageboard (comment posting)
- Server-side page generation for frontpage

## Setup
The backend assumes that some directories exist in /var/www/odysea by default.
This repo is currently very development-oriented as opposed to something polished
you can use to host your own ODYSEA server instance, so you're gonna need to look
at the code files a lot in case documentation or templates are missing. Please, 
only run this for testing, DO NOT use this for production in your own custom server 
instances as-is just yet, as it's missing important files needed for a fully-functional 
and secure instance. (Currently only we at odysea.us.to have those set up as intended,
and we're planning on making a full custom instance setup guide in the future.)

Install Obun:
```
git clone https://github.com/Dogo6647/obun.git
cd obun
./install.sh
```

Clone this repo and install requirements:
```
git clone https://github.com/htlabs-games/ods-backend.git
pip install -r requirements.txt
```

Run the backend:
```
cd ods-backend
obun -w
```

## API usage
We ask you to please make good use of our and other instances' APIs. While there are server-side limits set in place by default to prevent you from making too many requests or in places where you shouldn't at that time, you should take a moment to read the instance's guidelines and adhere to them in your application.

If you're the maintainer of an instance, you will notice that users' request value details will not be logged to protect their privacy and security.

For regular users: If a website asks you for your ODYSEA login details, DO NOT type them in unless you have at least done your research on the people behind it and trust them. They *will* gain full control over your account.

- POST /api/get-login-token/ `username` `password`
- POST /api/get-user-by-token/ `token`
- POST /api/logout/ `token`
- POST/GET /api/get-site-bar/ `cookie:web_login_token`
- POST /api/post-comment/ `token` `page_id` `comment_body`
- POST /api/upload-level/ `name` `description` `token` `file:data_file` `file:thumbnail (optional)`
- POST/GET /api/get-frontpage/ `data-category (newest|bestrated|mostplayed)`
- POST/GET /api/level-info/ `level`
- POST /api/speedtest/ `file:file`
