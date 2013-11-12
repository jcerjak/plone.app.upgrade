from Products.CMFCore.utils import getToolByName

from plone.app.upgrade.tests.base import MigrationTest

import alphas
from plone.registry.interfaces import IRegistry
from zope.component import queryUtility
from plone.app.controlpanel.interfaces import INavigationSchema
from plone.app.controlpanel.interfaces import IEditingSchema


class PASUpgradeTest(MigrationTest):

    def test_double_upgrade(self):
        # Check that calling our upgrade twice does no harm.
        alphas.lowercase_email_login(self.portal)
        alphas.lowercase_email_login(self.portal)

    def test_upgrade_with_email_login(self):
        pas = getToolByName(self.portal, 'acl_users')
        regtool = getToolByName(self.portal, 'portal_registration')
        regtool.addMember('JOE', 'somepassword')
        self.assertEqual(pas.getUserById('JOE').getUserName(), 'JOE')

        # First call.
        alphas.lowercase_email_login(self.portal)
        self.assertEqual(pas.getProperty('login_transform'), '')
        self.assertEqual(pas.getUserById('JOE').getUserName(), 'JOE')

        # If email as login is enabled, we want to use lowercase login
        # names, even when that login name is not an email address.
        ptool = getToolByName(self.portal, 'portal_properties')
        ptool.site_properties.manage_changeProperties(use_email_as_login=True)

        # Second call.
        alphas.lowercase_email_login(self.portal)
        self.assertEqual(pas.getProperty('login_transform'), 'lower')
        self.assertEqual(pas.getUserById('JOE').getUserName(), 'joe')

    def test_navigation_properties_to_registry(self):

        portal_setup = getToolByName(self.portal, 'portal_setup')
        portal_setup.runAllImportStepsFromProfile('profile-plone.app.controlpanel:default')
        registry = queryUtility(IRegistry)
        registry.registerInterface(INavigationSchema)
        registry.registerInterface(IEditingSchema)

        ttool = getToolByName(self.portal, 'portal_types')
        ptool = getToolByName(self.portal, 'portal_properties')
        siteProps = ptool['site_properties']
        navProps = ptool['navtree_properties']
        navProps.showAllParents = False
        alphas.navigation_properties_to_registry(self.portal)
        settings = registry.forInterface(INavigationSchema)
        self.assertTrue(not settings.generate_tabs == siteProps.disable_folder_sections)
        self.assertTrue(not settings.nonfolderish_tabs == siteProps.disable_nonfolderish_sections)

        allTypes = ttool.listContentTypes()
        displayed_types = tuple([
            t for t in allTypes \
            if t not in navProps.metaTypesNotToList])
        for t in displayed_types:
            self.assertTrue(t in settings.displayed_types)

        self.assertEqual(settings.filter_on_workflow, navProps.enable_wf_state_filtering)
        self.assertEqual(settings.workflow_states_to_show, navProps.wf_states_to_show)
        self.assertEqual(settings.show_excluded_items, navProps.showAllParents)
        self.assertTrue(not settings.show_excluded_items)


    def test_editing_properties_to_registry(self)

        portal_setup = getToolByName(self.portal, 'portal_setup')
        portal_setup.runAllImportStepsFromProfile('profile-plone.app.controlpanel:default')
        registry = queryUtility(IRegistry)
        registry.registerInterface(IEditingSchema)
        
        ptool = getToolByName(self.portal, 'portal_properties')
        siteProps = ptool['site_properties']
        alphas.navigation_properties_to_registry(self.portal)
        settings = registry.forInterface(IEditingSchema)
        
        for v in ('visible_ids', 'enable_link_integrity_checks', \
                  'ext_editor', 'default_editor', 'lock_on_ttw_edit'):  
            self.assertEqual(settings[v], siteProps[v])
        
        