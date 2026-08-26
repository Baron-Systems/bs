# -*- coding: utf-8 -*-
# Copyright (c) 2024, AL Baron Systems and contributors
# For license information, please see license.txt

"""
WWW page controller for /bs
Serves the built Vue 3 SPA from bs/public/frontend.

The built index.html already contains the correct entry <script> and <link> tags
with hashed filenames. We parse it to extract the asset URLs instead of guessing.
"""

import os
import re

import frappe


def _extract_assets_from_index(html):
	"""Extract JS entry scripts, modulepreloads, and CSS links from the built index.html."""
	js_files = []
	css_files = []

	# Entry module scripts: <script type="module" crossorigin src="..."></script>
	for m in re.finditer(r'<script[^>]*\bsrc="([^"]+\.js)"[^>]*>', html):
		src = m.group(1)
		if src not in js_files:
			js_files.append(src)

	# Module preloads: <link rel="modulepreload" href="...">
	for m in re.finditer(r'<link[^>]*\brel="modulepreload"[^>]*\bhref="([^"]+\.js)"', html):
		src = m.group(1)
		if src not in js_files:
			js_files.append(src)

	# Stylesheets: <link rel="stylesheet" href="...">
	for m in re.finditer(r'<link[^>]*\brel="stylesheet"[^>]*\bhref="([^"]+\.css)"', html):
		src = m.group(1)
		if src not in css_files:
			css_files.append(src)

	return js_files, css_files


def get_context(context):
	"""Inject CSRF token, user info, and built asset file lists into the Jinja context."""
	# User info (for boot)
	user = frappe.session.user
	user_fullname = ""
	user_image = ""

	if user and user != "Guest":
		try:
			user_fullname, user_image = frappe.db.get_value(
				"User", user, ["full_name", "user_image"]
			) or ("", "")
		except Exception:
			pass

	context.user = user
	context.user_fullname = user_fullname or ""
	context.user_image = user_image or ""
	context.csrf_token = frappe.sessions.get_csrf_token()

	# Read the built index.html to extract the correct entry assets
	frontend_dir = frappe.get_app_path("bs", "public", "frontend")
	index_path = os.path.join(frontend_dir, "index.html")

	js_files = []
	css_files = []

	if os.path.isfile(index_path):
		with open(index_path, "r", encoding="utf-8") as f:
			built_html = f.read()
		js_files, css_files = _extract_assets_from_index(built_html)

	context.css_files = css_files
	context.js_files = js_files

	# No index sidebar / caching
	context.no_cache = 1

	return context
