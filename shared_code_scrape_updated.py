# -*- coding: utf-8 -*-
"""
Created on Thu Aug 21 17:57:57 2025

@author: ntmy.423
"""

# %pip install requests
# %pip install beautifulsoup4 lxml pandas numpy openpyxl
# %%Import libraries.
import os, sys
import requests
from urllib.parse import urljoin, urlparse
from urllib.request import urlopen
import urllib.request
from bs4 import BeautifulSoup
import re
import pandas as pd
import numpy as np

# %%Import Jesse's LC. You can choose how you want to pull the file and put in the associated diectory and file name.
os.chdir('/Users/mynguyen/Downloads')

lc_df=pd.read_excel('DIGITIZED-LEGAL-COMPENDIUM-V2019.xlsx', engine='openpyxl')

#Read in statute file if it exists.
if os.path.exists('current_text_v1.csv'):
    main_df = pd.read_csv('current_text_v1.csv')
else:
    main_df = pd.DataFrame()

#Create df for matched statutes.
current_df=lc_df.loc[lc_df.backsources_2019==lc_df.backsources_2023]
current_df=current_df.loc[((current_df.backsources_2019.isnull()==False) & (pd.isnull(current_df.backsources_2023)==False))]
current_df=current_df.loc[((current_df.backsources_2023!='No') & (current_df.backsources_2023!='NO'))]

# %%Scrape statutes.
current_df['temp_statute']=current_df['statute_section'].astype('str')
current_df['temp_statute']=current_df['temp_statute'].replace('{SS}: ','',regex=True)
current_df['state']=current_df.state.str.lower()
current_df=current_df[current_df.state.notna()]
states=(current_df.state.unique()).tolist()
states.sort()
multi_state=current_df.loc[current_df.MULTI=='CHECK §§']
multi_state=multi_state.state.unique()

stat_split=dict(zip(states,['-','.','-','-','','-','-','','.','-','-','-','/','-','.','-','.',':','-','-','-','.','.','-','.','-','-','.',':',':','-','(','-','','.','-','','','','','','','','',' ','.','','-','.','-']))

stat_split=dict()
url_base='https://law.justia.com/codes/'
user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'

# %%Alabama.
s='alabama'
stat_split['alabama']='-'
url_state_year='alabama/2023/'

#Create df with statute pieces.
temp_df=current_df.loc[current_df.state=='alabama']
temp=temp_df['temp_statute'].str.split('-',expand=True)
temp.columns=['title','chapter','section']
temp['state']=s
temp=temp[['state','title','chapter','section']]

# Ensure output columns exist so they appear even before fetching
temp['statute_text']=''
temp['statute_mods']=''
temp['universal_citation']=''
# Ensure output columns exist even if fetch finds nothing
temp['statute_text']=''
temp['statute_mods']=''
temp['universal_citation']=''
temp[['section','subsection']]=temp['section'].str.split('.',expand=True)
temp['paragraph']=temp['section'].str.extract('\((.*)',expand=True)
temp['paragraph']='('+temp['paragraph']
temp['section']=temp['section'].str.split('(',expand=True)[0]
temp['section_url']=temp_df['temp_statute'].str.split('(',expand=True)[0]
temp['section_url']=temp['section_url'].str.replace('.','-')
temp=temp.applymap(lambda x: x.lower() if isinstance(x, str) else x)
parts=temp['paragraph'].str.split(r'\(', n=2)
for i in temp.index:
    if pd.isna(temp.loc[i,'paragraph'])==False:
        if len(parts[i])==2:
            temp.loc[i,'subparagraph_1']='('+temp.loc[i,'paragraph'].split("(", 2)[1]
        elif len(parts[i])==3:
            temp.loc[i,'subparagraph_1']='('+temp.loc[i,'paragraph'].split("(", 2)[1]
            temp.loc[i,'subparagraph_2']='('+temp.loc[i,'paragraph'].split("(", 2)[2]

temp['article']='NaN'
temp.loc[temp.title=='13a','article']='3'
temp.loc[temp.title=='10a','article']=temp['section']

#Create url for each statute.
temp['url']='title-'+temp['title']+'/chapter-'+temp['chapter']
temp.loc[temp['title'].str.contains('a'),'url']=temp['url']+'/'+'article-'+temp['article']
temp['url']=temp['url']+'/'+'section-'+temp['section_url']+'/'
temp['url']=url_base+url_state_year+temp['url']
temp=temp[temp.url.notna()]

#Get statute text.
for i in temp.index:
    url=temp.loc[i,'url']
    req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
    page = urlopen(req)
    html = page.read().decode("utf-8")
    soup = BeautifulSoup(html, "html.parser")

    #The main text for each statute is under the div ID 'codes-content' for Alabama.  Need to verify for other states.
    soup.find('div',id='codes-content').get_text()

    #This separates text into statute and previous amendments to statute.
    text=soup.find('div',id='codes-content')
    #text=text.get_text(separator='em>', strip=True).split('em>')
    mod_text=soup.find('em')
    if mod_text is None:
        mod_text=''
    else:
        mod_text=mod_text.get_text()
    text=text.get_text(separator='</p> <p>', strip=True).split('</p> <p>')
    temp.loc[i,'statute_text']=''.join(text)
    temp.loc[i,'statute_mods']=''.join(mod_text)
    #temp.loc[i,'statute_text']=''.join(text[:-1])
    #temp.loc[i,'statute_mods']=text[-1]
    
    '''
    if pd.isna(temp.loc[i,'subparagraph_1'])==False:
        temptext_1=temp.loc[i,'statute_text'].split('.'+temp.loc[i,'subparagraph_1']+' ')[1]
        temp.loc[i,'statute_text']=temptext_1
        if pd.isna(temp.loc[i,'subparagraph_2'])==False:
            temptext_2=temptext_1.split(temp.loc[i,'subparagraph_2']+' ')[1]
            temptext_2=temptext_2.split(".(")[0]
            temp.loc[i,'statute_text']=temptext_2
    '''        
    #This gets the universal citation.
    temp.loc[i,'universal_citation']=soup.find('div',class_='citation').find('span').get_text()

#This gets the heading for the statute, and puts each level in a list as separate element.
headings=[x for x in map(str.strip, (soup.find('h1').get_text()).split('.')) if x]

#Create df of statutes.
main_df=temp.copy()
main_df.reset_index(inplace=True)
main_df.to_csv('current_text_v1.csv',index=False)

#Merge text dataframe into original dataframe.
#final_df=pd.concat([current_df,temp],axis=1)


# %%Alaska.
s='alaska'
stat_split['alaska']='.'
url_state_year='alaska/2023/'
temp_df=current_df.loc[current_df.state=='alaska']
print(np.sum(temp_df['MULTI']=='CHECK §§'))
temp=temp_df['temp_statute'].str.split('.',expand=True)
temp.columns=['title','chapter','section']
temp['state']=s
temp=temp[['state','title','chapter','section']]
#temp[['section','subsection']]=temp['section'].str.split('.',expand=True)
temp['paragraph']=temp['section'].str.extract('\((.*)',expand=True)
temp['paragraph']='('+temp['paragraph']
temp['section']=temp['section'].str.split('(',expand=True)[0]
temp['section_url']=temp_df['temp_statute'].str.split('(',expand=True)[0]
temp['section_url']=temp['section_url'].str.replace('.','-')
temp=temp.applymap(lambda x: x.lower() if isinstance(x, str) else x)
parts = temp['paragraph'].str.split(r'\(', n=2)
for i in temp.index:
    if pd.isna(temp.loc[i,'paragraph'])==False:
        if len(parts[i])==2:
            temp.loc[i,'subparagraph_1']='('+temp.loc[i,'paragraph'].split("(", 2)[1]
        elif len(parts[i])==3:
            temp.loc[i,'subparagraph_1']='('+temp.loc[i,'paragraph'].split("(", 2)[1]
            temp.loc[i,'subparagraph_2']='('+temp.loc[i,'paragraph'].split("(", 2)[2]

temp['url']='title-'+temp['title']+'/chapter-'+temp['chapter']
temp=temp[temp.url.notna()]
temp['article']='NaN'
temp.loc[((temp.section.astype('int')<=141) & (temp.title.astype('int')==10)),'article']='1'
temp.loc[((temp.section.astype('int')>141) & (temp.section.astype('int')<=166) & (temp.title.astype('int')==10)),'article']='2'
temp.loc[((temp.section.astype('int')>166) & (temp.section.astype('int')<=211) & (temp.title.astype('int')==10)),'article']='3'
temp.loc[((temp.section.astype('int')>211) & (temp.section.astype('int')<=285) & (temp.title.astype('int')==10)),'article']='4'
temp.loc[((temp.section.astype('int')>285) & (temp.section.astype('int')<=452) & (temp.title.astype('int')==10)),'article']='5'
temp.loc[((temp.section.astype('int')>452) & (temp.section.astype('int')<=615) & (temp.title.astype('int')==10)),'article']='6'
temp.loc[((temp.section.astype('int')>615) & (temp.section.astype('int')<=631) & (temp.title.astype('int')==10)),'article']='7'
temp.loc[((temp.section.astype('int')>631) & (temp.section.astype('int')<=643) & (temp.title.astype('int')==10)),'article']='8'
temp.loc[((temp.section.astype('int')>643) & (temp.section.astype('int')<=650) & (temp.title.astype('int')==10)),'article']='9'
temp.loc[((temp.section.astype('int')>650) & (temp.section.astype('int')<=700) & (temp.title.astype('int')==10)),'article']='10'

#Create url for each statute.
#temp['url']='title-'+temp['title']+'/chapter-'+temp['chapter']
temp.loc[temp.title.astype('int')==10,'url']=temp['url']+'/'+'article-'+temp['article']
temp['url']=temp['url']+'/'+'section-'+temp['section_url']+'/'
temp['url']=url_base+url_state_year+temp['url']
temp=temp[temp.url.notna()]

#Get statute text.
for i in temp.index:
    url=temp.loc[i,'url']
    req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
    page = urlopen(req)
    html = page.read().decode("utf-8")
    soup = BeautifulSoup(html, "html.parser")
    soup.find('div',id='codes-content').get_text()

    #This separates text into statute and previous amendments to statute.
    text=soup.find('div',id='codes-content')
    mod_text=soup.find('em')
    if mod_text is None:
        mod_text=''
    else:
        mod_text=mod_text.get_text()
    #text=text.get_text(separator='em', strip=True).split('em')
    text=text.get_text(separator='</p> <p>', strip=True).split('</p> <p>')
    temp.loc[i,'statute_text']=''.join(text)
    temp.loc[i,'statute_mods']=''.join(mod_text)
    
    '''
    if pd.isna(temp.loc[i,'subparagraph_1'])==False:
        temptext_1=temp.loc[i,'statute_text'].split('.'+temp.loc[i,'subparagraph_1']+' ')[1]
        temp.loc[i,'statute_text']=temptext_1
        if pd.isna(temp.loc[i,'subparagraph_2'])==False:
            temptext_2=temptext_1.split(temp.loc[i,'subparagraph_2']+' ')[1]
            temptext_2=temptext_2.split(".(")[0]
            temp.loc[i,'statute_text']=temptext_2
    '''        
    #This gets the universal citation.
    temp.loc[i,'universal_citation']=soup.find('div',class_='citation').find('span').get_text()

#This gets the heading for the statute, and puts each level in a list as separate element.
headings=[x for x in map(str.strip, (soup.find('h1').get_text()).split('.')) if x]

#Merge into statute df and save.
temp.reset_index(inplace=True)
main_df=pd.concat([main_df,temp],ignore_index=True)
main_df.to_csv('current_text_v1.csv',index=False)

#Merge text dataframe into original dataframe.
#final_df=pd.concat([current_df,temp],axis=1,ignore_index=True)


# %%Arkansas. Needs more work.
stat_split['arkansas']='-'
s='arkansas'
url_state_year=s+'/2023/'
temp_df=current_df.loc[current_df.state==s]
print(np.sum(temp_df['MULTI']=='CHECK §§'))
temp=temp_df['temp_statute'].str.split(stat_split[s],expand=True)
temp.columns=['title','chapter','section']
temp['state']=s
temp=temp[['state','title','chapter','section']]
temp=temp[temp.title!='nan']
temp['subchapter']=temp['section'].str.split('(',expand=True)[0]
temp.loc[(temp.subchapter.str.len()==3),'subchapter']=temp['subchapter'].str[0]
temp.loc[(temp.subchapter.str.len()==4),'subchapter']=temp['subchapter'].str[:2]
temp['paragraph']=temp['section'].str.extract('\((.*)',expand=True)
temp['paragraph']='('+temp['paragraph']
temp['section']=temp['section'].str.split('(',expand=True)[0]
temp['section_url']=temp_df['temp_statute'].str.split('(',expand=True)[0]
temp['section_url']=temp['section_url'].str.replace('.','-')
temp['section_url']=temp['section_url'].str.rstrip()
temp=temp.applymap(lambda x: x.lower() if isinstance(x, str) else x)
parts = temp['paragraph'].str.split(r'\(', n=2)
for i in temp.index:
    if pd.isna(temp.loc[i,'paragraph'])==False:
        if len(parts[i])==2:
            temp.loc[i,'subparagraph_1']='('+temp.loc[i,'paragraph'].split("(", 2)[1]
        elif len(parts[i])==3:
            temp.loc[i,'subparagraph_1']='('+temp.loc[i,'paragraph'].split("(", 2)[1]
            temp.loc[i,'subparagraph_2']='('+temp.loc[i,'paragraph'].split("(", 2)[2]

temp['part']=np.nan
temp.loc[temp.subchapter=='14','part']='a'
temp.loc[((temp.subchapter=='14') & (temp.section.astype(int)>=1420) & (temp.section.astype(int)<=1424)),'part']='b'
temp.loc[((temp.subchapter=='14') & (temp.section.astype(int)>=1430) & (temp.section.astype(int)<=1434)),'part']='c'
temp.loc[((temp.subchapter=='14') & (temp.section=='1440')),'part']='d'
                
temp['url']='title-'+temp['title']+'/subtitle-3'+'/chapter-'+temp['chapter']+'/subchapter-'+temp['subchapter']+'/section-'+temp['section_url']+'/'
temp.loc[temp.subchapter=='14','url']='title-'+temp['title']+'/subtitle-3'+'/chapter-'+temp['chapter']+'/subchapter-'+temp['subchapter']+'/part-'+temp['part']+'/section-'+temp['section_url']+'/'
temp['url']=url_base+url_state_year+temp['url']
#Arkansas paragraphs are different. (a)(1)(A)

#Get statute text.
for i in temp.index:
        url=temp.loc[i,'url']
        req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
        page = urlopen(req)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        soup.find('div',id='codes-content').get_text()
    
        #This separates text into statute and previous amendments to statute.
        text=soup.find('div',id='codes-content')
        mod_text=soup.find('em')
        if mod_text is None:
            mod_text=''
        else:
            mod_text=mod_text.get_text()
        #text=text.get_text(separator='em', strip=True).split('em')
        text=text.get_text(separator='</p> <p>', strip=True).split('</p> <p>')
        temp.loc[i,'statute_text']=''.join(text)
        temp.loc[i,'statute_mods']=''.join(mod_text)
        
        #This gets the universal citation.
        temp.loc[i,'universal_citation']=soup.find('div',class_='citation').find('span').get_text()

temp.reset_index(inplace=True)
main_df=pd.concat([main_df,temp],ignore_index=True)
main_df.to_csv('current_text_v1.csv',index=False)




# %%Arizona. Paragraph letters are capitalized and followed by a period.
stat_split['arizona']='-'
s='arizona'
url_state_year=s+'/2023/'
temp_df=current_df.loc[current_df.state==s]
print(np.sum(temp_df['MULTI']=='CHECK §§'))
temp=temp_df['temp_statute'].str.split(stat_split[s],expand=True)
temp.columns=['title','section']
temp['state']=s
temp=temp[['state','title','section']]
temp=temp[temp.title!='nan']
temp['subchapter']=temp['section'].str.split('(',expand=True)[0]
temp.loc[(temp.subchapter.str.len()==3),'subchapter']=temp['subchapter'].str[0]
temp.loc[(temp.subchapter.str.len()==4),'subchapter']=temp['subchapter'].str[:2]
temp['paragraph']=temp['section'].str.extract('\((.*)',expand=True)
temp['paragraph']='('+temp['paragraph']
temp['section']=temp['section'].str.split('(',expand=True)[0]
temp['section_url']=temp_df['temp_statute'].str.split('(',expand=True)[0]
temp['section_url']=temp['section_url'].str.replace('.','-')
temp['section_url']=temp['section_url'].str.rstrip()
temp=temp.applymap(lambda x: x.lower() if isinstance(x, str) else x)
parts = temp['paragraph'].str.split(r'\(', n=2)
for i in temp.index:
    if pd.isna(temp.loc[i,'paragraph'])==False:
        if len(parts[i])==2:
            temp.loc[i,'subparagraph_1']='('+temp.loc[i,'paragraph'].split("(", 2)[1]
        elif len(parts[i])==3:
            temp.loc[i,'subparagraph_1']='('+temp.loc[i,'paragraph'].split("(", 2)[1]
            temp.loc[i,'subparagraph_2']='('+temp.loc[i,'paragraph'].split("(", 2)[2]

temp['url']='title-'+temp['title']+'/section-'+temp['section_url']+'/'
temp['url']=url_base+url_state_year+temp['url']

#Get statute text.
for i in temp.index:
        url=temp.loc[i,'url']
        req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
        page = urlopen(req)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        soup.find('div',id='codes-content').get_text()
    
        #This separates text into statute and previous amendments to statute.
        text=soup.find('div',id='codes-content')
        mod_text=soup.find('em')
        if mod_text is None:
            mod_text=''
        else:
            mod_text=mod_text.get_text()
        #text=text.get_text(separator='em', strip=True).split('em')
        text=text.get_text(separator='</p> <p>', strip=True).split('</p> <p>')
        temp.loc[i,'statute_text']=''.join(text)
        temp.loc[i,'statute_mods']=''.join(mod_text)
        
        #This gets the universal citation.
        temp.loc[i,'universal_citation']=soup.find('div',class_='citation').find('span').get_text()

temp.reset_index(inplace=True)
main_df=pd.concat([main_df,temp],ignore_index=True)
main_df.to_csv('current_text_v1.csv',index=False)
# %%California. Skip for now.


# %%Colorado. Paragraphs w/ lettering are preceded by semicolon, w/ numbers are preceded by ., but no trailing space. One of the subparagraphs has an extra ) at the end.  Still issues w/ some subparagraphs.
stat_split['colorado']='-'
s='colorado'
url_state_year=s+'/2023/'
temp_df=current_df.loc[current_df.state==s]
print(np.sum(temp_df['MULTI']=='CHECK §§'))
temp=temp_df['temp_statute'].str.split(stat_split[s],expand=True)
temp.columns=['title','article','section']
temp['state']=s
temp=temp[['state','title','article','section']]
temp['article_name']='charitable-solicitations/'
temp.loc[((temp.title=='6') & (temp.article=='19')),'article_name']='transactions-involving-licensed-hospitals/'
temp.loc[temp.title=='7','article_name']='corporations-continued/nonprofit-corporations/'
temp.loc[temp.title=='15','article_name']='fiduciary/'
temp.loc[temp.title=='24','article_name']='principal-departments/'

temp['part']=temp['section'].str.split('(',expand=True)[0]
temp.loc[(temp.part.str.len()==3),'part']=temp['part'].str[0]
temp.loc[(temp.part.str.len()==4),'part']=temp['part'].str[:2]

temp['paragraph']=temp['section'].str.extract('\((.*)',expand=True)
temp['paragraph']='('+temp['paragraph']
temp['section']=temp['section'].str.split('(',expand=True)[0]
temp['section_url']=temp_df['temp_statute'].str.split('(',expand=True)[0]
temp['section_url']=temp['section_url'].str.replace('.','-')
temp['section_url']=temp['section_url'].str.rstrip()

temp['url']='title-'+temp['title']+'/'+temp['article_name']+'article-'+temp['article']+'/part-'+temp['part']+'/section-'+temp['section_url']+'/'
temp.loc[((temp.title=='6') & (temp.article=='16')),'url']='title-'+temp['title']+'/'+temp['article_name']+'article-'+temp['article']+'/section-'+temp['section_url']+'/'
temp.loc[temp.article=='131','url']='title-'+temp['title']+'/'+temp['article_name']+'article-'+temp['article']+'/section-'+temp['section_url']+'/'
temp=temp[temp.url.notna()]
temp['url']=url_base+url_state_year+temp['url']

#Get statute text.
for i in temp.index:
        url=temp.loc[i,'url']
        req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
        page = urlopen(req)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        soup.find('div',id='codes-content').get_text()
    
        #This separates text into statute and previous amendments to statute.
        text=soup.find('div',id='codes-content')
        mod_text=soup.find('em')
        if mod_text is None:
            mod_text=''
        else:
            mod_text=mod_text.get_text()
        #text=text.get_text(separator='em', strip=True).split('em')
        text=text.get_text(separator='</p> <p>', strip=True).split('</p> <p>')
        temp.loc[i,'statute_text']=''.join(text)
        temp.loc[i,'statute_mods']=''.join(mod_text)
        
        #This gets the universal citation.
        temp.loc[i,'universal_citation']=soup.find('div',class_='citation').find('span').get_text()

temp.reset_index(inplace=True)
main_df=pd.concat([main_df,temp],ignore_index=True)
main_df.to_csv('current_text_v1.csv',index=False)



# %%Connecticut.
stat_split['connecticut']='-'
s='connecticut'
url_state_year=s+'/2023/'
temp_df=current_df.loc[current_df.state==s]
print(np.sum(temp_df['MULTI']=='CHECK §§'))
temp=temp_df['temp_statute'].str.split(stat_split[s],expand=True)
temp.columns=['title','section']
temp['state']=s
temp['chapter']=''
temp=temp[['state','title','chapter','section']]
temp=temp[temp.title!='nan']
temp['paragraph']=temp['section'].str.extract('\((.*)',expand=True)
temp['paragraph']='('+temp['paragraph']
temp['section']=temp['section'].str.split('(',expand=True)[0]
temp['section_url']=temp_df['temp_statute'].str.split('(',expand=True)[0]
temp['section_url']=temp['section_url'].str.replace('.','-')
temp['section_url']=temp['section_url'].str.rstrip()
temp=temp.applymap(lambda x: x.lower() if isinstance(x, str) else x)
parts = temp['paragraph'].str.split(r'\(', n=2)
for i in temp.index:
    if pd.isna(temp.loc[i,'paragraph'])==False:
        if len(parts[i])==2:
            temp.loc[i,'subparagraph_1']='('+temp.loc[i,'paragraph'].split("(", 2)[1]
        elif len(parts[i])==3:
            temp.loc[i,'subparagraph_1']='('+temp.loc[i,'paragraph'].split("(", 2)[1]
            temp.loc[i,'subparagraph_2']='('+temp.loc[i,'paragraph'].split("(", 2)[2]

temp.loc[temp.title=='21a','chapter']='419d'
temp.loc[temp.title=='19a','chapter']='368v'
temp.loc[temp.title=='33','chapter']='602'
temp.loc[((temp.title=='33') & (temp.section.str.contains('264'))),'chapter']='598'

temp['url']='title-'+temp['title']+'/chapter-'+temp['chapter']+'/section-'+temp['section_url']+'/'
temp['url']=url_base+url_state_year+temp['url']

#Get statute text.
for i in temp.index:
        url=temp.loc[i,'url']
        req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
        page = urlopen(req)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        soup.find('div',id='codes-content').get_text()
    
        #This separates text into statute and previous amendments to statute.
        text=soup.find('div',id='codes-content')
        text=text.get_text(separator='</p> <p>', strip=True).split('History:')
        temp.loc[i,'statute_text']=''.join(text[0])
        if len(text)==2:
            temp.loc[i,'statute_mods']=''.join(text[1])
        else:
            temp.loc[i,'statute_mods']=''
        
        #This gets the universal citation.
        temp.loc[i,'universal_citation']=soup.find('div',class_='citation').find('span').get_text()

temp.reset_index(inplace=True)
main_df=pd.concat([main_df,temp],ignore_index=True)
main_df.to_csv('current_text_v1.csv',index=False)


# %%Delaware. Do by hand for now.
stat_split['delaware']='-'
s='delaware'
url_state_year=s+'/2023/'

# %%DC. Skip for now.
stat_split['washington, d.c.']=''
s='washington, d.c.'
url_state_year=s+'/2023/'
temp_df=current_df.loc[current_df.state==s]
temp=temp_df['temp_statute'].str.split(stat_split[s],expand=True)

# %%Florida. Pretty sure 986 is a typo.
stat_split['florida']='.'
s='florida'
url_state_year=s+'/2023/'
temp_df=current_df.loc[current_df.state==s]
print(np.sum(temp_df['MULTI']=='CHECK §§'))
temp=temp_df['temp_statute'].str.split(stat_split[s],expand=True)
temp.columns=['chapter','section']
temp['state']=s
temp['title']=''
temp=temp[['state','title','chapter','section']]
temp=temp[temp.chapter!='nan']
temp['paragraph']=temp['section'].str.extract('\((.*)',expand=True)
temp['paragraph']='('+temp['paragraph']
temp['section']=temp['section'].str.split('(',expand=True)[0]
temp['section_url']=temp_df['temp_statute'].str.split('(',expand=True)[0]
temp['section_url']=temp['section_url'].str.replace('.','-')
temp['section_url']=temp['section_url'].str.rstrip()
temp=temp.applymap(lambda x: x.lower() if isinstance(x, str) else x)
parts = temp['paragraph'].str.split(r'\(', n=2)
for i in temp.index:
    if pd.isna(temp.loc[i,'paragraph'])==False:
        if len(parts[i])==2:
            temp.loc[i,'subparagraph_1']='('+temp.loc[i,'paragraph'].split("(", 2)[1]
        elif len(parts[i])==3:
            temp.loc[i,'subparagraph_1']='('+temp.loc[i,'paragraph'].split("(", 2)[1]
            temp.loc[i,'subparagraph_2']='('+temp.loc[i,'paragraph'].split("(", 2)[2]

temp['title']='xi'
temp.loc[temp.chapter=='496','title']='xxxiii'
temp.loc[temp.chapter=='617','title']='xxxvi'
temp=temp[temp.chapter!='986']

temp['url']='title-'+temp['title']+'/chapter-'+temp['chapter']+'/section-'+temp['section_url']+'/'
temp['url']=url_base+url_state_year+temp['url']

#Get statute text.
for i in temp.index:
        url=temp.loc[i,'url']
        req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
        page = urlopen(req)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        soup.find('div',id='codes-content').get_text()
    
        #This separates text into statute and previous amendments to statute.
        text=soup.find('div',id='codes-content')
        text=text.get_text().split('History.—')
        temp.loc[i,'statute_text']=''.join(text[0])
        if len(text)==2:
            temp.loc[i,'statute_mods']=''.join(text[1])
        else:
            temp.loc[i,'statute_mods']=''
        
        #This gets the universal citation.
        temp.loc[i,'universal_citation']=soup.find('div',class_='citation').find('span').get_text()

temp.reset_index(inplace=True)
main_df=pd.concat([main_df,temp],ignore_index=True)
main_df.to_csv('current_text_v1.csv',index=False)


# %%Georgia.
stat_split['georgia']='-'
s='georgia'
url_state_year=s+'/2023/'
temp_df=current_df.loc[current_df.state==s]
print(np.sum(temp_df['MULTI']=='CHECK §§'))
temp=temp_df['temp_statute'].str.split(stat_split[s],expand=True)
temp.columns=['title','chapter','section']
temp['state']=s
temp['article']=''
temp['part']=''
temp=temp[['state','title','chapter','article','part','section']]
temp.loc[temp.section.str.len()==3,'article']=temp.section.str[:1]
temp.loc[temp.section.str.len()==3,'part']=temp.section.str[1]
temp.loc[temp.section.str.len()==4,'article']=temp.section.str[:2]
temp.loc[temp.section.str.len()==4,'part']=temp.section.str[2]
temp.loc[temp.part=='0','part']='1'
temp.loc[temp.section=='170','part']='6'

temp=temp[temp.title!='nan']
temp['paragraph']=temp['section'].str.extract('\((.*)',expand=True)
temp['paragraph']='('+temp['paragraph']
temp['section']=temp['section'].str.split('(',expand=True)[0]
temp['section_url']=temp_df['temp_statute'].str.split('(',expand=True)[0]
temp['section_url']=temp['section_url'].str.replace('.','-')
temp['section_url']=temp['section_url'].str.rstrip()
temp=temp.applymap(lambda x: x.lower() if isinstance(x, str) else x)
parts = temp['paragraph'].str.split(r'\(', n=2)
for i in temp.index:
    if pd.isna(temp.loc[i,'paragraph'])==False:
        if len(parts[i])==2:
            temp.loc[i,'subparagraph_1']='('+temp.loc[i,'paragraph'].split("(", 2)[1]
        elif len(parts[i])==3:
            temp.loc[i,'subparagraph_1']='('+temp.loc[i,'paragraph'].split("(", 2)[1]
            temp.loc[i,'subparagraph_2']='('+temp.loc[i,'paragraph'].split("(", 2)[2]

temp['url']='title-'+temp['title']+'/chapter-'+temp['chapter']+'/section-'+temp['section_url']+'/'
temp.loc[temp.title=='14','url']='title-'+temp['title']+'/chapter-'+temp['chapter']+'/article-'+temp['article']+'/part-'+temp['part']+'/section-'+temp['section_url']+'/'
temp.loc[((temp.title=='14') & (temp.article=='11')),'url']='title-'+temp['title']+'/chapter-'+temp['chapter']+'/article-'+temp['article']+'/section-'+temp['section_url']+'/'
temp.loc[((temp.title=='14') & (temp.article=='12')),'url']='title-'+temp['title']+'/chapter-'+temp['chapter']+'/article-'+temp['article']+'/section-'+temp['section_url']+'/'
temp['url']=url_base+url_state_year+temp['url']

#Get statute text.
for i in temp.index:
        url=temp.loc[i,'url']
        req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
        page = urlopen(req)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        soup.find('div',id='codes-content').get_text()
    
        #This separates text into statute and previous amendments to statute.
        text=soup.find('div',id='codes-content')
        mod_text=soup.find('em')
        if mod_text is None:
            mod_text=''
        else:
            mod_text=mod_text.get_text()
        #text=text.get_text(separator='em', strip=True).split('em')
        text=text.get_text(separator='</p> <p>', strip=True).split('</p> <p>')
        temp.loc[i,'statute_text']=''.join(text)
        temp.loc[i,'statute_mods']=''.join(mod_text)
        
        #This gets the universal citation.
        temp.loc[i,'universal_citation']=soup.find('div',class_='citation').find('span').get_text()

temp.reset_index(inplace=True)
main_df=pd.concat([main_df,temp],ignore_index=True)
main_df.to_csv('current_text_v1.csv',index=False)


# %%Hawaii. Index 585 is 432c, but used to be 432c-2. Ask if it still should be.
stat_split['hawaii']='-'
s='hawaii'
url_state_year=s+'/2023/'
temp_df=current_df.loc[current_df.state==s]
print(np.sum(temp_df['MULTI']=='CHECK §§'))
temp=temp_df['temp_statute'].str.split(stat_split[s],expand=True)
temp.columns=['chapter','section']
temp['state']=s
temp['title']=''
temp=temp[['state','title','chapter','section']]
temp=temp[temp.chapter!='nan']
temp['paragraph']=temp['section'].str.extract('\((.*)',expand=True)
temp['paragraph']='('+temp['paragraph']
temp['section']=temp['section'].str.split('(',expand=True)[0]
temp['section_url']=temp_df['temp_statute'].str.split('(',expand=True)[0]
temp['section_url']=temp['section_url'].str.replace('.','-')
temp['section_url']=temp['section_url'].str.rstrip()
temp=temp.applymap(lambda x: x.lower() if isinstance(x, str) else x)
parts = temp['paragraph'].str.split(r'\(', n=2)
for i in temp.index:
    if pd.isna(temp.loc[i,'paragraph'])==False:
        if len(parts[i])==2:
            temp.loc[i,'subparagraph_1']='('+temp.loc[i,'paragraph'].split("(", 2)[1]
        elif len(parts[i])==3:
            temp.loc[i,'subparagraph_1']='('+temp.loc[i,'paragraph'].split("(", 2)[1]
            temp.loc[i,'subparagraph_2']='('+temp.loc[i,'paragraph'].split("(", 2)[2]

temp['title']='4'
temp.loc[temp.chapter=='414d','title']='23'
temp.loc[temp.chapter=='432c','title']='24'
temp.loc[temp.chapter=='467b','title']='25'


temp['url']='title-'+temp['title']+'/chapter-'+temp['chapter']+'/section-'+temp['section_url']+'/'
temp['url']=url_base+url_state_year+temp['url']

#Get statute text.
for i in temp.index:
        url=temp.loc[i,'url']
        req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
        page = urlopen(req)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        soup.find('div',id='codes-content').get_text()
    
        #This separates text into statute and previous amendments to statute.
        text=soup.find('div',id='codes-content')        
        text=text.get_text().split('[L')
        temp.loc[i,'statute_text']=''.join(text[0])
        if len(text)==2:
            temp.loc[i,'statute_mods']=''.join(text[1])
        else:
            temp.loc[i,'statute_mods']=''
            
        #This gets the universal citation.
        temp.loc[i,'universal_citation']=soup.find('div',class_='citation').find('span').get_text()

temp.reset_index(inplace=True)
main_df=pd.concat([main_df,temp],ignore_index=True)
main_df.to_csv('current_text_v1.csv',index=False)


# %%Idaho. Need to deal with multi statute flag.
stat_split['idaho']='-'
s='idaho'
url_state_year=s+'/2023/'
temp_df=current_df.loc[current_df.state==s]
print(np.sum(temp_df['MULTI']=='CHECK §§'))
temp=temp_df['temp_statute'].str.split(stat_split[s],expand=True)
temp.columns=['title','chapter','section']
temp['state']=s
temp=temp[['state','title','chapter','section']]
temp=temp[temp.title!='nan']
temp.loc[temp.title=='48','section']=temp['chapter']
temp.loc[temp.title=='48','chapter']='15'
temp['paragraph']=temp['section'].str.extract('\((.*)',expand=True)
temp['paragraph']='('+temp['paragraph']
temp['section']=temp['section'].str.split('(',expand=True)[0]
temp['section_url']=temp_df['temp_statute'].str.split('(',expand=True)[0]
temp['section_url']=temp['section_url'].str.replace('.','-')
temp['section_url']=temp['section_url'].str.rstrip()
temp=temp.applymap(lambda x: x.lower() if isinstance(x, str) else x)

temp.loc[temp.section.str.len()==3,'part']=temp.section.str[0]
temp.loc[temp.section.str.len()==4,'part']=temp.section.str[:2]
temp.loc[temp.title=='48','part']=''

temp['url']='title-'+temp['title']+'/chapter-'+temp['chapter']+'/section-'+temp['section_url']+'/'
temp.loc[temp.title=='30','url']='title-'+temp['title']+'/chapter-'+temp['chapter']+'/part-'+temp['part']+'/section-'+temp['section_url']+'/'
temp['url']=url_base+url_state_year+temp['url']

#Get statute text.
for i in temp.index:
        url=temp.loc[i,'url']
        req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
        page = urlopen(req)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        soup.find('div',id='codes-content').get_text()
    
        #This separates text into statute and previous amendments to statute.
        text=soup.find('div',id='codes-content')        
        text=text.get_text().split('History:')
        temp.loc[i,'statute_text']=''.join(text[0])
        if len(text)==2:
            temp.loc[i,'statute_mods']=''.join(text[1])
        else:
            temp.loc[i,'statute_mods']=''
            
        #This gets the universal citation.
        temp.loc[i,'universal_citation']=soup.find('div',class_='citation').find('span').get_text()

temp.reset_index(inplace=True)
main_df=pd.concat([main_df,temp],ignore_index=True)
main_df.to_csv('current_text_v1.csv',index=False)

# %%Illinois. Needs more work.
stat_split['illinois']='/'
s='illinois'
url_state_year=s+'/2023/'
temp_df=current_df.loc[current_df.state==s]
print(np.sum(temp_df['MULTI']=='CHECK §§'))
temp=temp_df['temp_statute'].str.split(stat_split[s],expand=True)
temp.columns=['act','section']
temp['state']=s
temp['chapter']=''
temp['article']=''
temp=temp[['state','chapter','act','article','section']]
print(temp_df.loc[temp_df.temp_statute=='nan','backsources_2023'])
temp=temp[temp_df.backsources_2023!='nan']
temp['chapter']=temp_df['backsources_2023'].str.extract(r'(\d+) ILCS', expand=False)
temp.loc[temp.chapter.isna(),'chapter']=temp_df['backsources_2023'].str.extract(r'(\d+) Ill. Comp. Stat.', expand=False)
temp.loc[temp.act=='nan','act']=temp_df['backsources_2023'].str.extract(r'(\d+)/', expand=False)
temp.loc[temp.section.isna(),'section']=temp_df['backsources_2023'].str.extract(r'/(\d+)', expand=False)
temp['article']=temp['section'].str.extract(r'(\d)')
temp.loc[((temp.chapter=='805') & (temp.act=='105')),'article']=temp.loc[((temp.chapter=='805') & (temp.act=='105')),'section'].str.extract(r'(\d+).')[0]
temp.loc[((temp.chapter=='805') & (temp.act=='105')),'article']=temp.loc[((temp.chapter=='805') & (temp.act=='105')),'article'].str[-2:]

temp['paragraph']=temp['section'].str.extract('\((.*)',expand=True)
temp['paragraph']='('+temp['paragraph']
temp['section']=temp['section'].str.split('(',expand=True)[0]
temp['section_url']=temp_df['temp_statute'].str.split('(',expand=True)[0]
temp['section_url']=temp['section_url'].str.replace('.','-')
temp['section_url']=temp['section_url'].str.rstrip()
temp=temp.applymap(lambda x: x.lower() if isinstance(x, str) else x)
parts = temp['paragraph'].str.split(r'\(', n=2)
for i in temp.index:
    if pd.isna(temp.loc[i,'paragraph'])==False:
        if len(parts[i])==2:
            temp.loc[i,'subparagraph_1']='('+temp.loc[i,'paragraph'].split("(", 2)[1]
        elif len(parts[i])==3:
            temp.loc[i,'subparagraph_1']='('+temp.loc[i,'paragraph'].split("(", 2)[1]
            temp.loc[i,'subparagraph_2']='('+temp.loc[i,'paragraph'].split("(", 2)[2]

temp['url']='chapter-'+temp['chapter']+'/act-'+temp['chapter']+'-ilcs-'+temp['act']+'/'
temp.loc[temp.chapter=='805','url']='chapter-'+temp['chapter']+'/act-'+temp['chapter']+'-ilcs-'+temp['act']+'/article-'+temp['article']+'/'
temp['url']=url_base+url_state_year+temp['url']

#Get statute text.
for i in temp.index:
    if i!=730:
        url=temp.loc[i,'url']
        req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
        page = urlopen(req)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        soup.find('div',id='codes-content').get_text()
    
        #This separates text into statute and previous amendments to statute.
        text=soup.find('div',id='codes-content')
        text=text.get_text().split('('+temp.loc[i,'chapter']+' ILCS '+temp.loc[i,'act']+'/'+temp.loc[i,'section']+')')[1]
        text=text.split('(Source:')
        temp.loc[i,'statute_text']=''.join(text[0])
        temp.loc[i,'statute_mods']=''.join(text[1].split(')')[0])
 
        #This gets the universal citation.
        #temp.loc[i,'universal_citation']=soup.find('div',class_='citation').find('span').get_text()

temp.reset_index(inplace=True)
main_df=pd.concat([main_df,temp],ignore_index=True)
main_df.to_csv('current_text_v1.csv',index=False)





# %%Indiana.
stat_split['indiana']='-'
s='indiana'
url_state_year=s+'/2023/'
temp_df=current_df.loc[current_df.state==s]
print(np.sum(temp_df['MULTI']=='CHECK §§'))
temp_df.loc[temp_df.temp_statute=='nan','temp_statute']=temp_df['backsources_2023'].str.split('IC ').str[1]
temp_df.loc[temp_df.temp_statute=='I.C','temp_statute']=temp_df['backsources_2023'].str.split('I.C. ').str[1]
temp=temp_df['temp_statute'].str.split(stat_split[s],expand=True)
temp.columns=['title','article','chapter','section']
temp['state']=s
temp=temp[['state','title','article','chapter','section']]
print(temp_df.loc[temp_df.temp_statute=='nan','backsources_2023'])
temp=temp[temp_df.backsources_2023!='nan']

temp['paragraph']=temp['section'].str.extract('\((.*)',expand=True)
temp['paragraph']='('+temp['paragraph']
temp['section']=temp['section'].str.split('(',expand=True)[0]
temp['section_url']=temp_df['temp_statute'].str.split('(',expand=True)[0]
temp['section_url']=temp['section_url'].str.replace('.','-')
temp['section_url']=temp['section_url'].str.rstrip()
temp=temp.applymap(lambda x: x.lower() if isinstance(x, str) else x)

temp['url']='title-'+temp['title']+'/article-'+temp['article']+'/chapter-'+temp['chapter']+'/section-'+temp['section_url']+'/'
temp['url']=url_base+url_state_year+temp['url']

#Get statute text.
for i in temp.index:
        url=temp.loc[i,'url']
        req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
        page = urlopen(req)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        soup.find('div',id='codes-content').get_text()
    
        #This separates text into statute and previous amendments to statute.
        text=soup.find('div',id='codes-content')
        mod_text=soup.find('em')
        if mod_text is None:
            mod_text=''
        else:
            mod_text=mod_text.get_text()
        #text=text.get_text(separator='em', strip=True).split('em')
        text=text.get_text().split('As added by')
        temp.loc[i,'statute_text']=''.join(text[0])
        temp.loc[i,'statute_mods']=''.join(mod_text)
        
        #This gets the universal citation.
        temp.loc[i,'universal_citation']=soup.find('div',class_='citation').find('span').get_text()

temp.reset_index(inplace=True)
main_df=pd.concat([main_df,temp],ignore_index=True)
main_df.to_csv('current_text_v1.csv',index=False)


# %%Iowa.
stat_split['iowa']='.'
s='iowa'
url_state_year=s+'/2023/'
temp_df=current_df.loc[current_df.state==s]
print(np.sum(temp_df['MULTI']=='CHECK §§'))
temp=temp_df['temp_statute'].str.split(stat_split[s],expand=True)
temp.columns=['chapter','section']
temp['state']=s
temp['title']='i'
temp=temp[['state','title','chapter','section']]
print(temp_df.loc[temp_df.temp_statute=='nan','backsources_2023'])
temp=temp[temp_df.backsources_2023!='nan']
temp.loc[temp.chapter=='504','title']='xii'
temp.loc[temp.chapter=='633A','title']='xv'

temp['paragraph']=temp['section'].str.extract('\((.*)',expand=True)
temp['paragraph']='('+temp['paragraph']
temp['section']=temp['section'].str.split('(',expand=True)[0]
temp['section_url']=temp_df['temp_statute'].str.split('(',expand=True)[0]
temp['section_url']=temp['section_url'].str.replace('.','-')
temp['section_url']=temp['section_url'].str.rstrip()
temp=temp.applymap(lambda x: x.lower() if isinstance(x, str) else x)

temp['url']='title-'+temp['title']+'/chapter-'+temp['chapter']+'/section-'+temp['section_url']+'/'
temp['url']=url_base+url_state_year+temp['url']

#Get statute text.
for i in temp.index:
        url=temp.loc[i,'url']
        req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
        page = urlopen(req)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        soup.find('div',id='codes-content').get_text()
    
        #This separates text into statute and previous amendments to statute.
        text=soup.find('div',id='codes-content')
        if temp.loc[i,'chapter']=='504':
            text=text.get_text().split('2004 Acts')
            temp.loc[i,'statute_mods']='2004 Acts'+''.join(text[1])
        elif temp.loc[i,'chapter']=='13c':
            text=text.get_text().split('[S13')
            temp.loc[i,'statute_mods']='[S13'+''.join(text[1])
        else:
            text=text.get_text().split('2009 Acts')
            temp.loc[i,'statute_mods']='2009 Acts'+''.join(text[1])
        
        temp.loc[i,'statute_text']=''.join(text[0])

        #This gets the universal citation.
        temp.loc[i,'universal_citation']=soup.find('div',class_='citation').find('span').get_text()

temp.reset_index(inplace=True)
main_df=pd.concat([main_df,temp],ignore_index=True)
main_df.to_csv('current_text_v1.csv',index=False)


# %%Kansas. Not sure what this means KSA 17-1759 - 17-1776.
stat_split['kansas']='-'
s='kansas'
url_state_year=s+'/2023/'
temp_df=current_df.loc[current_df.state==s]
print(np.sum(temp_df['MULTI']=='CHECK §§'))
temp=temp_df['temp_statute'].str.split(stat_split[s],expand=True)
temp.columns=['chapter','section']
temp['state']=s
temp=temp[['state','chapter','section']]
print(temp_df.loc[temp_df.temp_statute=='nan','backsources_2023'])
temp=temp[temp_df.backsources_2023!='nan']
temp['article']=temp.section.str[:2]

temp['paragraph']=temp['section'].str.extract('\((.*)',expand=True)
temp['paragraph']='('+temp['paragraph']
temp['section']=temp['section'].str.split('(',expand=True)[0]
temp['section_url']=temp_df['temp_statute'].str.split('(',expand=True)[0]
temp['section_url']=temp['section_url'].str.replace('.','-')
temp['section_url']=temp['section_url'].str.rstrip()
temp=temp.applymap(lambda x: x.lower() if isinstance(x, str) else x)

temp['url']='chapter-'+temp['chapter']+'/article-'+temp['article']+'/section-'+temp['section_url']+'/'
temp['url']=url_base+url_state_year+temp['url']

#Get statute text.
for i in temp.index:
    if pd.isnull(temp.loc[i,'url'])==False:
        url=temp.loc[i,'url']
        req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
        page = urlopen(req)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        soup.find('div',id='codes-content').get_text()
    
        #This separates text into statute and previous amendments to statute.
        text=soup.find('div',id='codes-content')
        #text=text.get_text(separator='em', strip=True).split('em')
        text=text.get_text().split('History:')
        temp.loc[i,'statute_text']=''.join(text[0])
        temp.loc[i,'statute_mods']='History:'+''.join(text[1])
        
        #This gets the universal citation.
        temp.loc[i,'universal_citation']=soup.find('div',class_='citation').find('span').get_text()

temp.reset_index(inplace=True)
main_df=pd.concat([main_df,temp],ignore_index=True)
main_df.to_csv('current_text_v1.csv',index=False)

# %%Kentucky. Do by hand for now.
stat_split['kentucky']='.'
s='kentucky'
url_state_year=s+'/2023/'
temp_df=current_df.loc[current_df.state==s]


# %%Louisiana. La. Admin Code Title 16 was last amended 9/2015. 
#See here https://www.doa.la.gov/doa/osr/louisiana-administrative-code/
#La. Rev. Stat. Ann. 40:2115.11  40:2115.23 refers to all statutes in between according to LC.
#Still needs work.
stat_split['louisiana']=':'
s='louisiana'
url_state_year=s+'/2023/revised-statutes/'
temp_df=current_df.loc[current_df.state==s]
print(np.sum(temp_df['MULTI']=='CHECK §§'))
temp_df.loc[temp_df.backsources_2023.str.contains('La. Admin Code.'),'temp_statute']=temp_df['backsources_2023'].str.split('Code. ').str[1]
temp=temp_df['temp_statute'].str.split(stat_split[s],expand=True)
temp.columns=['title','section']
temp['state']=s
temp=temp[['state','title','section']]
print(temp_df.loc[temp_df.temp_statute=='nan','backsources_2023'])
temp.loc[temp_df.backsources_2023.str.contains('La. Admin Code.'),'section']=temp_df.temp_statute.str.split('§ ').str[1]
#temp=temp[temp_df.backsources_2023!='nan']

temp['paragraph']=temp['section'].str.extract('\((.*)',expand=True)
temp['paragraph']='('+temp['paragraph']
temp['section']=temp['section'].str.split('(',expand=True)[0]
temp['section_url']=temp_df['temp_statute'].str.split('(',expand=True)[0]
temp['section_url']=temp['section_url'].str.replace(':','-')
temp['section_url']=temp['section_url'].str.replace('.','-')
temp['section_url']=temp['section_url'].str.rstrip()
temp=temp.applymap(lambda x: x.lower() if isinstance(x, str) else x)

temp['url']='title-'+temp['title']+'/rs-'+temp['section_url']+'/'
temp['url']=url_base+url_state_year+temp['url']
temp.loc[temp_df.backsources_2023.str.contains('La. Admin Code.'),'url']='https://regulations.justia.com/states/louisiana/title-16/part-iii/chapter-5/section-iii-515/'

#Get statute text.
for i in temp.index:
    if pd.isnull(temp.loc[i,'section'])==False:
        url=temp.loc[i,'url']
        req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
        page = urlopen(req)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        soup.find('div',id='codes-content').get_text()
    
        #This separates text into statute and previous amendments to statute.
        text=soup.find('div',id='codes-content')
        #text=text.get_text(separator='em', strip=True).split('em')
        if url=='https://regulations.justia.com/states/louisiana/title-16/part-iii/chapter-5/section-iii-515/':
            text=text.get_text().split('AUTHORITY NOTE:')
            temp.loc[i,'statute_mods']='AUTHORITY NOTE:'+''.join(text[1])
        else:
            text=text.get_text(separator='</p> <p>', strip=True).split('</p> <p>Acts')
            text[0]=text[0].replace('</p> <p>','')
            temp.loc[i,'statute_mods']='Acts '+''.join(text[1])

        temp.loc[i,'statute_text']=''.join(text[0])

        #This gets the universal citation.
        temp.loc[i,'universal_citation']=soup.find('div',class_='citation').find('span').get_text()

temp.reset_index(inplace=True)
main_df=pd.concat([main_df,temp],ignore_index=True)
main_df.to_csv('current_text_v1.csv',index=False)


# %%Maine. Multi issue.
stat_split['maine']='-'
s='maine'
url_state_year=s+'/2023/'
temp_df=current_df.loc[current_df.state==s]
print(np.sum(temp_df['MULTI']=='CHECK §§'))
temp=temp_df['temp_statute'].str.split(stat_split[s],expand=True)
temp.columns=['section_1','section_2']
temp['state']=s
temp['title']='13-b'
temp['part']=''
temp['chapter']=''
temp.loc[((temp.title=='13-b') & (temp.section_1.str.len()==3)),'chapter']=temp.section_1.str[0]
temp.loc[((temp.title=='13-b') & (temp.section_1.str.len()==4)),'chapter']=temp.section_1.str[:2]
temp.loc[temp['section_1']=='194',['title','part','chapter']]=['5','1','9']
temp.loc[temp['section_1'].str.contains('50'),['title','part','chapter']]=['9','13','385']
temp['section']=temp_df['temp_statute']
temp=temp[['state','title','part','chapter','section']]
print(temp_df.loc[temp_df.temp_statute=='nan','backsources_2023'])

temp['paragraph']=temp['section'].str.extract('\((.*)',expand=True)
temp['paragraph']='('+temp['paragraph']
temp['section']=temp['section'].str.split('(',expand=True)[0]
temp['section_url']=temp_df['temp_statute'].str.split('(',expand=True)[0]
temp['section_url']=temp['section_url'].str.replace('.','-')
temp['section_url']=temp['section_url'].str.rstrip()
temp=temp.applymap(lambda x: x.lower() if isinstance(x, str) else x)

temp['url']='title-'+temp['title']+'/part-'+temp['part']+'/chapter-'+temp['chapter']+'/section-'+temp['section_url']+'/'
temp.loc[temp.title=='13-b','url']='title-'+temp['title']+'/chapter-'+temp['chapter']+'/section-'+temp['section_url']+'/'
temp['url']=url_base+url_state_year+temp['url']

#Get statute text.
for i in temp.index:
    if pd.isnull(temp.loc[i,'url'])==False:
        url=temp.loc[i,'url']
        req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
        page = urlopen(req)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        soup.find('div',id='codes-content').get_text()
    
        #This separates text into statute and previous amendments to statute.
        text=soup.find('div',id='codes-content')
        #text=text.get_text(separator='em', strip=True).split('em')
        text=text.get_text().split('SECTION HISTORY')
        temp.loc[i,'statute_text']=''.join(text[0])
        temp.loc[i,'statute_mods']=''.join(text[1])
        
        #This gets the universal citation.
        temp.loc[i,'universal_citation']=soup.find('div',class_='citation').find('span').get_text()

temp.reset_index(inplace=True)
main_df=pd.concat([main_df,temp],ignore_index=True)
main_df.to_csv('current_text_v1.csv',index=False)

# %%Maryland. One does not have a section code, only the title. No statute mods.
stat_split['maryland']='-'
s='maryland'
url_state_year=s+'/2023/'
temp_df=current_df.loc[current_df.state==s]
print(np.sum(temp_df['MULTI']=='CHECK §§'))
temp=temp_df['temp_statute'].str.split(stat_split[s],expand=True)
temp.columns=['title','section']
temp['title']=temp['title'].str.replace('.','-')
temp['state']=s
temp['statute_name']='business-regulation'
temp.loc[temp_df.backsources_2023.str.contains('State Gov'),'statute_name']='state-government'
temp.loc[temp_df.backsources_2023.str.contains('MD Code, Corporations and Associations'),'statute_name']='corporations-and-associations'
temp['subtitle']=temp['section'].str[0]
temp=temp[['state','statute_name','title','subtitle','section']]
print(temp_df.loc[temp_df.temp_statute=='nan','backsources_2023'])

temp['paragraph']=temp['section'].str.extract('\((.*)',expand=True)
temp['paragraph']='('+temp['paragraph']
temp['section']=temp['section'].str.split('(',expand=True)[0]
temp['section_url']=temp_df['temp_statute'].str.split('(',expand=True)[0]
temp['section_url']=temp['section_url'].str.replace('.','-')
temp['section_url']=temp['section_url'].str.rstrip()
temp=temp.applymap(lambda x: x.lower() if isinstance(x, str) else x)

temp['url']=temp['statute_name']+'/title-'+temp['title']+'/subtitle-'+temp['subtitle']+'/section-'+temp['section_url']+'/'
temp['url']=url_base+url_state_year+temp['url']

#Get statute text.
for i in temp.index:
    if pd.isnull(temp.loc[i,'section'])==False:
        url=temp.loc[i,'url']
        req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
        page = urlopen(req)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        soup.find('div',id='codes-content').get_text()
    
        #This separates text into statute and previous amendments to statute.
        text=soup.find('div',id='codes-content')
        #text=text.get_text(separator='em', strip=True).split('em')
        text=text.get_text()
        temp.loc[i,'statute_text']=''.join(text)
        #temp.loc[i,'statute_mods']=''.join(text[1])
        
        #This gets the universal citation.
        temp.loc[i,'universal_citation']=soup.find('div',class_='citation').find('span').get_text()

temp.reset_index(inplace=True)
main_df=pd.concat([main_df,temp],ignore_index=True)
main_df.to_csv('current_text_v1.csv',index=False)

# %%Massachusetts. Multi issue.
stat_split['massachusetts']='-'
s='massachusetts'
url_state_year=s+'/2023/'
temp_df=current_df.loc[current_df.state==s]
print(np.sum(temp_df['MULTI']=='CHECK §§'))
temp=temp_df['temp_statute'].str.split(stat_split[s],expand=True)
temp.columns=['section']
temp['state']=s
temp['chapter']=temp_df['statute_chap_title'].astype('str')
temp['chapter']=temp['chapter'].replace('Chap. ','',regex=True)
temp.loc[((temp.chapter=='nan') & (temp.section!='nan')),'chapter']='180'
temp['part']='i'
temp['title']='ii'
temp.loc[temp.chapter=='68','title']='xi'
temp.loc[temp.chapter=='180','title']='xxii'
temp=temp[['state','part','title','chapter','section']]
print(temp_df.loc[temp_df.temp_statute=='nan','backsources_2023'])

temp['paragraph']=temp['section'].str.extract('\((.*)',expand=True)
temp['paragraph']='('+temp['paragraph']
temp['section']=temp['section'].str.split('(',expand=True)[0]
temp['section_url']=temp_df['temp_statute'].str.split('(',expand=True)[0]
temp['section_url']=temp['section_url'].str.replace('.','-')
temp['section_url']=temp['section_url'].str.rstrip()
temp=temp.applymap(lambda x: x.lower() if isinstance(x, str) else x)

temp['url']='part-'+temp['part']+'/title-'+temp['title']+'/chapter-'+temp['chapter']+'/section-'+temp['section_url']+'/'
temp['url']=url_base+url_state_year+temp['url']

#Get statute text.
for i in temp.index:
    if temp.loc[i,'chapter']!='nan':
        url=temp.loc[i,'url']
        req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
        page = urlopen(req)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        soup.find('div',id='codes-content').get_text()
    
        #This separates text into statute and previous amendments to statute.
        text=soup.find('div',id='codes-content')
        #text=text.get_text(separator='em', strip=True).split('em')
        text=text.get_text()
        temp.loc[i,'statute_text']=''.join(text)
        #temp.loc[i,'statute_mods']=''.join(text[1])
        
        #This gets the universal citation.
        temp.loc[i,'universal_citation']=soup.find('div',class_='citation').find('span').get_text()

temp.reset_index(inplace=True)
main_df=pd.concat([main_df,temp],ignore_index=True)
main_df.to_csv('current_text_v1.csv',index=False)

# %%Michigan. Needs more work.
stat_split['michigan']='.'
s='michigan'
url_state_year=s+'/2023/'
temp_df=current_df.loc[current_df.state==s]
print(np.sum(temp_df['MULTI']=='CHECK §§'))
temp=temp_df['temp_statute'].str.split(stat_split[s],expand=True)
temp.columns=['chapter','section']
temp['state']=s

temp.loc[((temp.chapter=='nan') & (temp.section!='nan')),'chapter']='180'
temp['part']='i'
temp['title']='ii'
temp.loc[temp.chapter=='68','title']='xi'
temp.loc[temp.chapter=='180','title']='xxii'
temp=temp[['state','part','title','chapter','section']]
print(temp_df.loc[temp_df.temp_statute=='nan','backsources_2023'])

temp['paragraph']=temp['section'].str.extract('\((.*)',expand=True)
temp['paragraph']='('+temp['paragraph']
temp['section']=temp['section'].str.split('(',expand=True)[0]
temp['section_url']=temp_df['temp_statute'].str.split('(',expand=True)[0]
temp['section_url']=temp['section_url'].str.replace('.','-')
temp['section_url']=temp['section_url'].str.rstrip()
temp=temp.applymap(lambda x: x.lower() if isinstance(x, str) else x)

temp['url']='part-'+temp['part']+'/title-'+temp['title']+'/chapter-'+temp['chapter']+'/section-'+temp['section_url']+'/'
temp['url']=url_base+url_state_year+temp['url']

#Get statute text.
for i in temp.index:
    if temp.loc[i,'chapter']!='nan':
        url=temp.loc[i,'url']
        req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
        page = urlopen(req)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        soup.find('div',id='codes-content').get_text()
    
        #This separates text into statute and previous amendments to statute.
        text=soup.find('div',id='codes-content')
        #text=text.get_text(separator='em', strip=True).split('em')
        text=text.get_text()
        temp.loc[i,'statute_text']=''.join(text)
        #temp.loc[i,'statute_mods']=''.join(text[1])
        
        #This gets the universal citation.
        temp.loc[i,'universal_citation']=soup.find('div',class_='citation').find('span').get_text()

temp.reset_index(inplace=True)
main_df=pd.concat([main_df,temp],ignore_index=True)
main_df.to_csv('current_text_v1.csv',index=False)

# %%Minnesota.
stat_split['minnesota']='.'
s='minnesota'
url_state_year=s+'/2023/'
temp_df=current_df.loc[current_df.state==s]
print(np.sum(temp_df['MULTI']=='CHECK §§'))
print(temp_df.loc[temp_df.temp_statute=='nan','backsources_2023'])
print(f"Texas temp_df shape: {temp_df.shape}")
if temp_df.empty:
    # Fall back to 2023 backsources directly if no matching 2019/2023 pair exists
    temp_df = lc_df.loc[
        (lc_df.state.str.lower()==s)
        & (lc_df['backsources_2023'].astype(str).str.strip().str.lower().isin(['', 'no'])==False)
        & (lc_df['backsources_2023'].notna())
    ].copy()
    temp_df['temp_statute'] = temp_df['statute_section'].astype('str')
    print(f"Texas fallback temp_df shape: {temp_df.shape}")
print(f"Texas temp_df shape: {temp_df.shape}")
if temp_df.empty:
    print("Texas temp_df is empty; falling back to lc_df for Texas")
    temp_df = lc_df.loc[lc_df.state.str.lower()==s].copy()
    if 'temp_statute' not in temp_df.columns:
        temp_df['temp_statute'] = temp_df['statute_section'].astype('str')
    if 'backsources_2023' not in temp_df.columns or temp_df['backsources_2023'].isna().all():
        if 'backsources_2019' in temp_df.columns:
            temp_df['backsources_2023'] = temp_df['backsources_2019']
        else:
            temp_df['backsources_2023'] = ''

# Fallback if no Texas rows in current_df
if temp_df.empty:
    print("Texas temp_df is empty; falling back to lc_df for Texas rows")
    temp_df = lc_df.loc[lc_df.state.str.lower()==s].copy()
    if 'temp_statute' not in temp_df.columns:
        temp_df['temp_statute'] = temp_df['statute_section'].astype('str')
    if 'backsources_2023' not in temp_df.columns or temp_df['backsources_2023'].isna().all():
        if 'backsources_2019' in temp_df.columns:
            temp_df['backsources_2023'] = temp_df['backsources_2019']
        else:
            temp_df['backsources_2023'] = ''
print(f"Texas temp_df shape: {temp_df.shape}")
if temp_df.empty:
    print("Texas temp_df is empty; falling back to lc_df for Texas")
    temp_df = lc_df.loc[lc_df.state.str.lower()==s].copy()
    temp_df['temp_statute'] = temp_df['statute_section'].astype('str')
    if ('backsources_2023' not in temp_df.columns) or (temp_df['backsources_2023'].isna().all()):
        if 'backsources_2019' in temp_df.columns:
            temp_df['backsources_2023'] = temp_df['backsources_2019']
        else:
            temp_df['backsources_2023'] = ''
temp_df.loc[temp_df.temp_statute=='nan','temp_statute']=temp_df['backsources_2023'].apply(lambda x: x[x.find('M.S.A. ') + len('M.S.A. ') : x.find(':')])
temp=temp_df['temp_statute'].str.split(stat_split[s],expand=True)
temp.columns=['chapter','section']
temp['state']=s
temp=temp[['state','chapter','section']]

temp['paragraph']=temp['section'].str.extract('\((.*)',expand=True)
temp['paragraph']='('+temp['paragraph']
temp['section']=temp['section'].str.split('(',expand=True)[0]
temp['section_url']=temp_df['temp_statute'].str.split('(',expand=True)[0]
temp['section_url']=temp['section_url'].str.replace('.','-')
temp['section_url']=temp['section_url'].str.rstrip()
temp=temp.applymap(lambda x: x.lower() if isinstance(x, str) else x)
temp.loc[((temp.chapter=='317a') & (temp.section=='61')),'section_url']='317a-061'

temp['url']='chapters-'+'300-323a'+'/chapter-'+temp['chapter']+'/section-'+temp['section_url']+'/'
temp['url']=url_base+url_state_year+temp['url']

#Get statute text.
for i in temp.index:
    if temp.loc[i,'chapter']!='':
        url=temp.loc[i,'url']
        req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
        page = urlopen(req)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        soup.find('div',id='codes-content').get_text()
    
        #This separates text into statute and previous amendments to statute.
        text=soup.find('div',id='codes-content')
        #text=text.get_text(separator='em', strip=True).split('em')
        text=text.get_text().split('History:')
        temp.loc[i,'statute_text']=''.join(text[0])
        temp.loc[i,'statute_mods']='History:'+''.join(text[1])
        
        #This gets the universal citation.
        temp.loc[i,'universal_citation']=soup.find('div',class_='citation').find('span').get_text()

temp.reset_index(inplace=True)
main_df=pd.concat([main_df,temp],ignore_index=True)
main_df.to_csv('current_text_v1.csv',index=False)

# %%Mississippi. Multi issue. Miss. Code Ann. § 79-11-5 doesn't exist. Must be a typo.
stat_split['mississippi']='-'
s='mississippi'
url_state_year=s+'/2023/'
temp_df=current_df.loc[current_df.state==s]
print(np.sum(temp_df['MULTI']=='CHECK §§'))
print(temp_df.loc[temp_df.temp_statute=='nan','backsources_2023'])
temp=temp_df['temp_statute'].str.split(stat_split[s],expand=True)
temp.columns=['title','chapter','section']
temp['state']=s
temp=temp[['state','title','chapter','section']]

temp['paragraph']=temp['section'].str.extract('\((.*)',expand=True)
temp['paragraph']='('+temp['paragraph']
temp['section']=temp['section'].str.split('(',expand=True)[0]
temp['section_url']=temp_df['temp_statute'].str.split('(',expand=True)[0]
temp['section_url']=temp['section_url'].str.replace('.','-')
temp['section_url']=temp['section_url'].str.rstrip()
temp=temp.applymap(lambda x: x.lower() if isinstance(x, str) else x)
temp['section_name']='regulation-of-charitable-solicitations'
temp.loc[((temp.section.astype('int')>=101) & (temp.section.astype('int')<=405)),'section_name']='mississippi-nonprofit-corporation-act'

temp['url']='title-'+temp['title']+'/chapter-'+temp['chapter']+'/'+temp['section_name']+'/section-'+temp['section_url']+'/'
temp['url']=url_base+url_state_year+temp['url']

#Get statute text.
for i in temp.index:
    #Temporary if condition.
    if temp.loc[i,'section']!='5':
        url=temp.loc[i,'url']
        req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
        page = urlopen(req)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        soup.find('div',id='codes-content').get_text()
    
        #This separates text into statute and previous amendments to statute.
        text=soup.find('div',id='codes-content')
        mod_text=soup.find('em')
        if mod_text is None:
            mod_text=''
        else:
            mod_text=mod_text.get_text()

        text=text.get_text().split('Laws,')
        temp.loc[i,'statute_text']=''.join(text[0])
        temp.loc[i,'statute_mods']=''.join(mod_text)
        
        #This gets the universal citation.
        temp.loc[i,'universal_citation']=soup.find('div',class_='citation').find('span').get_text()

temp.reset_index(inplace=True)
main_df=pd.concat([main_df,temp],ignore_index=True)
main_df.to_csv('current_text_v1.csv',index=False)

# %%Missouri. One missing.
stat_split['missouri']='.'
s='missouri'
url_state_year=s+'/2023/'
temp_df=current_df.loc[current_df.state==s]
print(np.sum(temp_df['MULTI']=='CHECK §§'))
print(temp_df.loc[temp_df.temp_statute=='nan','backsources_2023'])
temp=temp_df['temp_statute'].str.split(stat_split[s],expand=True)
temp.columns=['chapter','section']
temp['state']=s
temp['title']='xxiii'
temp.loc[temp.chapter=='407','title']='xxvi'
temp=temp[['state','title','chapter','section']]

temp['paragraph']=temp['section'].str.extract('\((.*)',expand=True)
temp['paragraph']='('+temp['paragraph']
temp['section']=temp['section'].str.split('(',expand=True)[0]
temp['section_url']=temp_df['temp_statute'].str.split('(',expand=True)[0]
temp['section_url']=temp['section_url'].str.replace('.','-')
temp['section_url']=temp['section_url'].str.rstrip()
temp=temp.applymap(lambda x: x.lower() if isinstance(x, str) else x)

temp['url']='title-'+temp['title']+'/chapter-'+temp['chapter']+'/section-'+temp['section_url']+'/'
temp['url']=url_base+url_state_year+temp['url']

#Get statute text.
for i in temp.index:
    #Temporary if condition.
    if temp.loc[i,'section_url']!='nan':
        url=temp.loc[i,'url']
        req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
        page = urlopen(req)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        soup.find('div',id='codes-content').get_text()
    
        #This separates text into statute and previous amendments to statute.
        text=soup.find('div',id='codes-content')
        text=text.get_text().split('--------')
        temp.loc[i,'statute_text']=''.join(text[0])
        temp.loc[i,'statute_mods']=''.join(text[1])
        
        #This gets the universal citation.
        temp.loc[i,'universal_citation']=soup.find('div',class_='citation').find('span').get_text()

temp.reset_index(inplace=True)
main_df=pd.concat([main_df,temp],ignore_index=True)
main_df.to_csv('current_text_v1.csv',index=False)

# %%Montana. Multi issue.
stat_split['montana']='-'
s='montana'
url_state_year=s+'/2023/'
temp_df=current_df.loc[current_df.state==s]
print(np.sum(temp_df['MULTI']=='CHECK §§'))
print(temp_df.loc[temp_df.temp_statute=='nan','backsources_2023'])
temp_df.loc[temp_df.temp_statute=='nan','temp_statute']=temp_df.loc[temp_df.temp_statute=='nan','backsources_2023'].str.split('M.C.A. ',expand=True)[1]
temp=temp_df['temp_statute'].str.split(stat_split[s],expand=True)
temp.columns=['title','chapter','section']
temp['state']=s
temp=temp[['state','title','chapter','section']]
temp['part']=temp['section'].str.split('(',expand=True)[0]
temp.loc[(temp.part.str.len()==3),'part']=temp['part'].str[0]
temp.loc[(temp.part.str.len()==4),'part']=temp['part'].str[:2]

temp['paragraph']=temp['section'].str.extract('\((.*)',expand=True)
temp['paragraph']='('+temp['paragraph']
temp['section']=temp['section'].str.split('(',expand=True)[0]
temp['section_url']=temp_df['temp_statute'].str.split('(',expand=True)[0]
temp['section_url']=temp['section_url'].str.replace('.','-')
temp['section_url']=temp['section_url'].str.rstrip()
temp=temp.applymap(lambda x: x.lower() if isinstance(x, str) else x)

temp['url']='title-'+temp['title']+'/chapter-'+temp['chapter']+'/part-'+temp['part']+'/section-'+temp['section_url']+'/'
temp['url']=url_base+url_state_year+temp['url']

#Get statute text.
for i in temp.index:
    if temp.loc[i,'section_url']!='nan' and pd.notna(temp.loc[i,'section_url']):
        url=temp.loc[i,'url']
        req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
        page = urlopen(req)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        soup.find('div',id='codes-content').get_text()
    
        #This separates text into statute and previous amendments to statute.
        text=soup.find('div',id='codes-content')
        text=text.get_text().split('History:')
        temp.loc[i,'statute_text']=''.join(text[0])
        temp.loc[i,'statute_mods']='History:'+''.join(text[1])
        
        #This gets the universal citation.
        temp.loc[i,'universal_citation']=soup.find('div',class_='citation').find('span').get_text()

temp.reset_index(inplace=True)
main_df=pd.concat([main_df,temp],ignore_index=True)
main_df.to_csv('current_text_v1.csv',index=False)

# %%Nebraska. Multi issue.
stat_split['nebraska']='-'
s='nebraska'
url_state_year=s+'/2023/'
temp_df=current_df.loc[current_df.state==s]
print(np.sum(temp_df['MULTI']=='CHECK §§'))
print(temp_df.loc[temp_df.temp_statute=='nan','backsources_2023'])
temp=temp_df['temp_statute'].str.split(stat_split[s],expand=True)
temp.columns=['chapter','section']
temp['state']=s
temp=temp[['state','chapter','section']]
temp=temp[temp_df.temp_statute!='nan']

temp['paragraph']=temp['section'].str.extract('\((.*)',expand=True)
temp['paragraph']='('+temp['paragraph']
temp['section']=temp['section'].str.split('(',expand=True)[0]
temp['section_url']=temp_df['temp_statute'].str.split('(',expand=True)[0]
temp['section_url']=temp['section_url'].str.replace('.','-')
temp['section_url']=temp['section_url'].str.replace(',','-')
temp['section_url']=temp['section_url'].str.rstrip()
temp=temp.applymap(lambda x: x.lower() if isinstance(x, str) else x)

temp['url']='chapter-'+temp['chapter']+'/statute-'+temp['section_url']+'/'
temp['url']=url_base+url_state_year+temp['url']

#Get statute text.
for i in temp.index:
    if temp.loc[i,'section_url']!='nan':
        url=temp.loc[i,'url']
        req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
        page = urlopen(req)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        soup.find('div',id='codes-content').get_text()
    
        #This separates text into statute and previous amendments to statute.
        text=soup.find('div',id='codes-content')
        text=text.get_text().split('Source')
        temp.loc[i,'statute_text']=''.join(text[0])
        temp.loc[i,'statute_mods']=''.join(text[1])
        
        #This gets the universal citation.
        temp.loc[i,'universal_citation']=soup.find('div',class_='citation').find('span').get_text()

temp.reset_index(inplace=True)
main_df=pd.concat([main_df,temp],ignore_index=True)
main_df.to_csv('current_text_v1.csv',index=False)

# %%Nevada. One observation uses this for a source, but it returns a search portal http://nvsos.gov/index.aspx?page=113.
stat_split['nevada']='.'
s='nevada'
url_state_year=s+'/2023/'
temp_df=current_df.loc[current_df.state==s]
print(np.sum(temp_df['MULTI']=='CHECK §§'))
print(temp_df.loc[temp_df.temp_statute=='nan','backsources_2023'])
temp_df.loc[temp_df.temp_statute=='nan','temp_statute']=temp_df.backsources_2023.str.split('NV ST ',expand=True)[1]
temp=temp_df['temp_statute'].str.split(stat_split[s],expand=True)
temp.columns=['chapter','section']
temp['state']=s
temp=temp[['state','chapter','section']]

temp['paragraph']=temp['section'].str.extract('\((.*)',expand=True)
temp['paragraph']='('+temp['paragraph']
temp['section']=temp['section'].str.split('(',expand=True)[0]
temp['section_url']=temp_df['temp_statute'].str.split('(',expand=True)[0]
temp['section_url']=temp['section_url'].str.replace('.','-')
temp['section_url']=temp['section_url'].str.replace(',','-')
temp['section_url']=temp['section_url'].str.rstrip()
temp=temp.applymap(lambda x: x.lower() if isinstance(x, str) else x)

temp['url']='chapter-'+temp['chapter']+'/statute-'+temp['section_url']+'/'
temp['url']=url_base+url_state_year+temp['url']

#Get statute text.
for i in temp.index:
    if pd.isnull(temp.loc[i,'section_url'])==False:
        url=temp.loc[i,'url']
        req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
        page = urlopen(req)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        soup.find('div',id='codes-content').get_text()
    
        #This separates text into statute and previous amendments to statute.
        text=soup.find('div',id='codes-content')
        text=text.get_text().split('(Added to')
        temp.loc[i,'statute_text']=''.join(text[0])
        temp.loc[i,'statute_mods']='(Added to'+''.join(text[1])
        
        #This gets the universal citation.
        temp.loc[i,'universal_citation']=soup.find('div',class_='citation').find('span').get_text()

temp.reset_index(inplace=True)
main_df=pd.concat([main_df,temp],ignore_index=True)
main_df.to_csv('current_text_v1.csv',index=False)

# %%New Hampshire.
stat_split['new hampshire']=':'
s='new hampshire'
url_state_year=s.replace(' ','-')+'/2023/'
temp_df=current_df.loc[current_df.state==s]
print(np.sum(temp_df['MULTI']=='CHECK §§'))
print(temp_df.loc[temp_df.temp_statute=='nan','backsources_2023'])
temp=temp_df['temp_statute'].str.split(stat_split[s],expand=True)
temp.columns=['chapter','section']
temp['state']=s
temp['title']='xxvii'
temp.loc[temp.chapter=='7','title']='i'
temp=temp[['state','title','chapter','section']]

temp['paragraph']=temp['section'].str.extract('\((.*)',expand=True)
temp['paragraph']='('+temp['paragraph']
temp['section']=temp['section'].str.split('(',expand=True)[0]
temp['section_url']=temp_df['temp_statute'].str.split('(',expand=True)[0]
temp['section_url']=temp['section_url'].str.replace('.','-')
temp['section_url']=temp['section_url'].str.replace(':','-')
temp['section_url']=temp['section_url'].str.rstrip()
temp=temp.applymap(lambda x: x.lower() if isinstance(x, str) else x)

temp['url']='title-'+temp['title']+'/chapter-'+temp['chapter']+'/section-'+temp['section_url']+'/'
temp['url']=url_base+url_state_year+temp['url']

#Get statute text.
for i in temp.index:
    if pd.isnull(temp.loc[i,'section_url'])==False:
        url=temp.loc[i,'url']
        req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
        page = urlopen(req)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        soup.find('div',id='codes-content').get_text()
    
        #This separates text into statute and previous amendments to statute.
        text=soup.find('div',id='codes-content')
        text=text.get_text().split('Source. ')
        temp.loc[i,'statute_text']=''.join(text[0])
        temp.loc[i,'statute_mods']='Source. '+''.join(text[1])
        
        #This gets the universal citation.
        temp.loc[i,'universal_citation']=soup.find('div',class_='citation').find('span').get_text()

temp.reset_index(inplace=True)
main_df=pd.concat([main_df,temp],ignore_index=True)
main_df.to_csv('current_text_v1.csv',index=False)

# %%New Jersey.Some obs. have the following url for source, but it is not a statute.
#http://www.njconsumeraffairs.gov/charities
stat_split['new jersey']=':'
s='new jersey'
url_state_year=s.replace(' ','-')+'/2023/'
temp_df=current_df.loc[current_df.state==s]
print(np.sum(temp_df['MULTI']=='CHECK §§'))
print(temp_df.loc[temp_df.temp_statute=='nan','backsources_2023'])
temp_df.loc[((temp_df.temp_statute=='nan') & (temp_df.backsources_2023.str.contains('45:17A-26\(d\)'))),'temp_statute']='45:17A-26(d)'
temp=temp_df['temp_statute'].str.split(stat_split[s],expand=True)
temp.columns=['title','section']
temp['state']=s
temp=temp[['state','title','section']]

temp['paragraph']=temp['section'].str.extract('\((.*)',expand=True)
temp['paragraph']='('+temp['paragraph']
temp['section']=temp['section'].str.split('(',expand=True)[0]
temp['section_url']=temp_df['temp_statute'].str.split('(',expand=True)[0]
temp['section_url']=temp['section_url'].str.replace('.','-')
temp['section_url']=temp['section_url'].str.replace(':','-')
temp['section_url']=temp['section_url'].str.rstrip()
temp=temp.applymap(lambda x: x.lower() if isinstance(x, str) else x)

temp['url']='title-'+temp['title']+'/section-'+temp['section_url']+'/'
temp['url']=url_base+url_state_year+temp['url']

#Get statute text.
for i in temp.index:
    if temp.loc[i,'section_url']!='nan':
        url=temp.loc[i,'url']
        req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
        page = urlopen(req)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        soup.find('div',id='codes-content').get_text()
    
        #This separates text into statute and previous amendments to statute.
        text=soup.find('div',id='codes-content')
        text=text.get_text(separator='</p><p>').split('</p><p> ')
        temp.loc[i,'statute_text']=''.join(text[:-1])
        temp.loc[i,'statute_mods']=''.join(text[-1])
        
        #This gets the universal citation.
        temp.loc[i,'universal_citation']=soup.find('div',class_='citation').find('span').get_text()

temp.reset_index(inplace=True)
main_df=pd.concat([main_df,temp],ignore_index=True)
main_df.to_csv('current_text_v1.csv',index=False)


# %%New Mexico. Annotations after amendments, how should we deal with them.
stat_split['new mexico']='-'
s='new mexico'
url_state_year=s.replace(' ','-')+'/2023/'
temp_df=current_df.loc[current_df.state==s]
print(np.sum(temp_df['MULTI']=='CHECK §§'))
print(temp_df.loc[temp_df.temp_statute=='nan','backsources_2023'])
temp=temp_df['temp_statute'].str.split(stat_split[s],expand=True)
temp.columns=['chapter','article','section']
temp['state']=s
temp=temp[['state','chapter','article','section']]

temp['paragraph']=temp['section'].str.extract('\((.*)',expand=True)
temp['paragraph']='('+temp['paragraph']
temp['section']=temp['section'].str.split('(',expand=True)[0]
temp['section_url']=temp_df['temp_statute'].str.split('(',expand=True)[0]
temp['section_url']=temp['section_url'].str.replace('.','-')
temp['section_url']=temp['section_url'].str.rstrip()
temp=temp.applymap(lambda x: x.lower() if isinstance(x, str) else x)

temp['url']='chapter-'+temp['chapter']+'/article-'+temp['article']+'/section-'+temp['section_url']+'/'
temp['url']=url_base+url_state_year+temp['url']

#Get statute text.
for i in temp.index:
    if temp.loc[i,'section_url']!='nan':
        url=temp.loc[i,'url']
        req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
        page = urlopen(req)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        soup.find('div',id='codes-content').get_text()
    
        #This separates text into statute and previous amendments to statute.
        text=soup.find('div',id='codes-content')
        text=text.get_text().split('History:')
        temp.loc[i,'statute_text']=''.join(text[0])
        temp.loc[i,'statute_mods']=''.join(text[1])
        
        #This gets the universal citation.
        temp.loc[i,'universal_citation']=soup.find('div',class_='citation').find('span').get_text()

temp.reset_index(inplace=True)
main_df=pd.concat([main_df,temp],ignore_index=True)
main_df.to_csv('current_text_v1.csv',index=False)

# %%New York. Multi Issue. The multi issue can cause 'law_name' to overlap too. One of the nan obs. doesn't have the statute anywhere, just 'Yes'. The other names all of article 9.
stat_split['new york']='('
s='new york'
url_state_year=s.replace(' ','-')+'/2023/'
temp_df=current_df.loc[current_df.state==s]
print(np.sum(temp_df['MULTI']=='CHECK §§'))
print(temp_df.loc[temp_df.temp_statute=='nan','backsources_2023'])
temp=temp_df['temp_statute'].str.split(stat_split[s],expand=True)
temp.columns=['section','paragraph','p2','p3']
temp.loc[pd.isnull(temp.paragraph)==False,'paragraph']='('+temp['paragraph']
temp.loc[pd.isnull(temp.p2)==False,'paragraph']=temp['paragraph']+'('+temp['p2']
temp.loc[pd.isnull(temp.p3)==False,'paragraph']=temp['paragraph']+'('+temp['p3']
temp['state']=s
temp['law_name']='ept'
temp.loc[temp_df.statute_label=='Exec. Law','law_name']='exc'
temp.loc[temp_df.statute_label=='NP Corp. Law','law_name']='npc'
temp.loc[temp.section.str.contains('8-1.4'),'law_name']='ept'

temp['article']='7-a'
temp.loc[temp.law_name=='ept','article']='8'
temp.loc[((temp.law_name=='npc') & (temp.section.str.len()==3)),'article']=temp['section'].str[0]
temp.loc[((temp.law_name=='npc') & (temp.section.str.len()==4)),'article']=temp['section'].str[:2]
temp.loc[temp_df.MULTI=='CHECK §§','article']=''

temp['part']=''
temp.loc[temp.law_name=='ept','part']='1'
temp.loc[temp_df.MULTI=='CHECK §§','part']=''

temp=temp[['state','law_name','article','part','section','paragraph']]

temp['section_url']=temp['section']
temp['section_url']=temp['section_url'].str.replace('.','-')
temp['section_url']=temp['section_url'].str.rstrip()
temp=temp.applymap(lambda x: x.lower() if isinstance(x, str) else x)

temp['url']=temp['law_name']+'/article-'+temp['article']+'/'+temp['section_url']+'/'
temp.loc[temp.law_name=='ept','url']=temp['law_name']+'/article-'+temp['article']+'/part-'+temp['part']+'/'+temp['section_url']+'/'
temp['url']=url_base+url_state_year+temp['url']

#Get statute text.
for i in temp.index:
    if (temp_df.loc[i,'MULTI']!='CHECK §§') & (temp.loc[i,'section_url']!='nan'):
    #if temp.loc[i,'section_url']!='nan':
        url=temp.loc[i,'url']
        req=urllib.request.Request(url,headers={'User-Agent': user_agent,})
        page = urlopen(req)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        soup.find('div',id='codes-content').get_text()
    
        #This separates text into statute and previous amendments to statute.
        text=soup.find('div',id='codes-content')
        text=text.get_text()
        temp.loc[i,'statute_text']=''.join(text)
        temp.loc[i,'statute_mods']=''
        
        #This gets the universal citation.
        temp.loc[i,'universal_citation']=soup.find('div',class_='citation').find('span').get_text()

temp.reset_index(inplace=True)
main_df=pd.concat([main_df,temp],ignore_index=True)
main_df.to_csv('current_text_v1.csv',index=False)

# %%North Carolina. Multi issue. One obs. cites https://www.secretary.state.nc.us/csl/. The other missing obs. has text instead of statute. One obs doesn't have a section number.
stat_split['north carolina']='-' 
s='north carolina'
url_state_year=s.replace(' ','-')+'/2023/'
temp_df=current_df.loc[current_df.state==s]
print(np.sum(temp_df['MULTI']=='CHECK §§'))
print(temp_df.loc[temp_df.temp_statute=='nan','backsources_2023'])
temp=temp_df['temp_statute'].str.split(stat_split[s],expand=True)
print(f"\nNumber of columns after split: {temp.shape[1]}")

temp.columns=['chapter','article','section']
temp['state']=s
temp=temp[['state','chapter','article','section']]
temp.loc[temp.chapter=='131F','section']=temp['article']
temp.loc[pd.isnull(temp.article),'section']='0'

temp['paragraph']=temp['section'].str.extract('\((.*)',expand=True)
temp['paragraph']='('+temp['paragraph']
temp['section']=temp['section'].str.split('(',expand=True)[0]

temp.loc[((temp.chapter=='131F') & (temp.section.astype('int')>=1)),'article']='1'
temp.loc[((temp.chapter=='131F') & (temp.section.astype('int')>=5)),'article']='2'
temp.loc[((temp.chapter=='131F') & (temp.section.astype('int')>=15)),'article']='3'
temp.loc[((temp.chapter=='131F') & (temp.section.astype('int')>=20)),'article']='4'
temp.loc[((temp.chapter=='131F') & (temp.section.astype('int')>=30)),'article']='5'

temp['section_url']=temp_df['temp_statute'].str.split('(',expand=True)[0]
temp['section_url']=temp['section_url'].str.replace('.','-')
temp['section_url']=temp['section_url'].str.rstrip()
temp=temp.map(lambda x: x.lower() if isinstance(x, str) else x)

temp['url']='chapter-'+temp['chapter']+'/article-'+temp['article']+'/section-'+temp['section_url']+'/'
temp['url']=url_base+url_state_year+temp['url']

#Get statute text.
for i in temp.index:
    if pd.isnull(temp.loc[i,'article'])==False:
        url=temp.loc[i,'url']
        print(f"Fetching: {url}")
        req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
        page = urlopen(req)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        soup.find('div',id='codes-content').get_text()
    
        #This separates text into statute and previous amendments to statute.
        text=soup.find('div',id='codes-content')
        text=re.split(r'(\(\d{4})', text.get_text())
        temp.loc[i,'statute_text']=''.join(text[:-2])
        temp.loc[i,'statute_mods']=''.join(text[-2:])
        
        #This gets the universal citation.
        temp.loc[i,'universal_citation']=soup.find('div',class_='citation').find('span').get_text()

temp.reset_index(inplace=True)
main_df=pd.concat([main_df,temp],ignore_index=True)
main_df.to_csv('current_text_v1.csv',index=False)

# %%North Dakota. Do by hand for now.


# %%Ohio. Admin code last updated 1/7/23.
stat_split['ohio']='.'
s='ohio'
url_state_year=s.replace(' ','-')+'/2023/'
temp_df=current_df.loc[current_df.state==s]
print(np.sum(temp_df['MULTI']=='CHECK §§'))
print(temp_df.loc[temp_df.temp_statute=='nan','backsources_2023'])
temp=temp_df['temp_statute'].str.split(stat_split[s],expand=True)
temp.columns=['chapter','section']
temp['title']=''
temp['state']=s
temp=temp[['state','title','chapter','section']]

temp.loc[temp.chapter.str.len()==3,'title']=temp['chapter'].str[0]
temp.loc[temp.chapter.str.len()==4,'title']=temp['chapter'].str[:2]

temp.loc[temp_df.backsources_2023=='Ohio Administrative Code 109:1-1-02(B)(1)',['title','chapter','section']]=['109-1','109-1-1','109-1-1-02']

temp['paragraph']=temp['section'].str.extract('\((.*)',expand=True)
temp['paragraph']='('+temp['paragraph']
temp['section']=temp['section'].str.split('(',expand=True)[0]
temp['section_url']=temp_df['temp_statute'].str.split('(',expand=True)[0]
temp['section_url']=temp['section_url'].str.replace('.','-')
temp['section_url']=temp['section_url'].str.rstrip()
temp.loc[temp_df.backsources_2023=='Ohio Administrative Code 109:1-1-02(B)(1)','section_url']='109-1-1-02'
temp=temp.applymap(lambda x: x.lower() if isinstance(x, str) else x)

temp['url']='title-'+temp['title']+'/chapter-'+temp['chapter']+'/section-'+temp['section_url']+'/'
temp.loc[temp_df.backsources_2023!='Ohio Administrative Code 109:1-1-02(B)(1)','url']=url_base+url_state_year+temp['url']
temp.loc[temp_df.backsources_2023=='Ohio Administrative Code 109:1-1-02(B)(1)','url']='https://regulations.justia.com/states/ohio/'+temp['url']

#Get statute text.
for i in temp.index:
    if temp.loc[i,'section_url']!='nan':
        url=temp.loc[i,'url']
        req=urllib.request.Request(url,headers={'User-Agent': user_agent,})
        page = urlopen(req)
        #page = urlopen(url)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        soup.find('div',id='codes-content').get_text()
    
        #This separates text into statute and previous amendments to statute.
        text=soup.find('div',id='codes-content')
        if temp_df.loc[i,'backsources_2023']=='Ohio Administrative Code 109:1-1-02(B)(1)':
            text=text.get_text().replace('\t', '').replace('\n','')
            temp.loc[i,'statute_text']=''.join(text)
            temp.loc[i,'statute_mods']=''
            temp.loc[i,'universal_citation']=soup.find('div',class_='has-margin-bottom-20').get_text()
        else:
            text=text.get_text(separator='<strong>',strip=True).split('<strong>')
            temp.loc[i,'statute_text']=''.join(text[4:])
            temp.loc[i,'statute_mods']=''.join(text[:4])
            temp.loc[i,'universal_citation']=soup.find('div',class_='citation').find('span').get_text()

temp.reset_index(inplace=True)
main_df=pd.concat([main_df,temp],ignore_index=True)
main_df.to_csv('current_text_v1.csv',index=False)

# %%Oklahoma.  One obs. only has 522 for the section code, but this is not an individual statute.  The other missing obs. only cites https://www.sos.ok.gov/(S(rxow5nrnwbjxrg45rwhhhg45))/charity/Default.aspx for the statute. 
stat_split['oklahoma']='-'  # Changed from '-' to '.'
s='oklahoma'
url_state_year=s+'/2023/'
temp_df=current_df.loc[current_df.state==s]
print(np.sum(temp_df['MULTI']=='CHECK §§'))
print(temp_df.loc[temp_df.temp_statute=='nan','backsources_2023'])
temp=temp_df['temp_statute'].str.split(stat_split[s],expand=True)
temp.columns=['section']
temp['title']='18'

# Handle the case where we only get section numbers
'''
if temp.shape[1] == 1:
    # Only section numbers - add default title
    temp.columns=['section']
    temp['title'] = '18'  # Default title for Oklahoma
elif temp.shape[1] == 2:
    # Has both parts (like 552.1 -> ['552', '1'])
    temp.columns=['section_part1','section_part2']
    temp['title'] = '18'
    # Reconstruct the full section
    temp['section'] = temp['section_part1'] + '.' + temp['section_part2']
else:
    # More than 2 parts - take first as section
    temp.columns = ['section'] + [f'part_{i}' for i in range(temp.shape[1]-1)]
    temp['title'] = '18'
'''

temp['state']=s
temp=temp[['state','title','section']]
temp['paragraph']=temp['section'].str.extract('\((.*)',expand=True)
temp['paragraph']='('+temp['paragraph']
temp['section']=temp['section'].str.split('(',expand=True)[0]
temp['section_url']=temp['section'].str.replace('.','-')
temp['section_url']=temp['section_url'].str.replace(':','-')
temp['section_url']=temp['section_url'].str.rstrip()
temp=temp.applymap(lambda x: x.lower() if isinstance(x, str) else x)  # Fixed deprecated applymap

# Oklahoma URL pattern on Justia:
# https://law.justia.com/codes/oklahoma/2023/title-18/section-18-552-4/
temp['url'] = 'title-' + temp['title'] + '/section-' + temp['title'] + '-' + temp['section_url'] + '/'
temp['url']=url_base + url_state_year + temp['url']
temp = temp[temp['url'].notna()]

# Initialize main_df if it doesn't exist
if 'main_df' not in locals():
    main_df = pd.DataFrame()

#Get statute text.
for i in temp.index:
    if pd.isnull(temp.loc[i,'section_url'])==False:
        url=temp.loc[i,'url']
        print(f"Fetching: {url}")  # Debug: see what URLs are being fetched
        
        try:
            req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
            page = urlopen(req)
            html = page.read().decode("utf-8")
            soup = BeautifulSoup(html, "html.parser")
            
            # Check if the content div exists
            content_div = soup.find('div',id='codes-content')
            if content_div is None:
                print(f"No content div found for {url}")
                temp.loc[i,'statute_text'] = "No content found"
                temp.loc[i,'statute_mods'] = ''
                temp.loc[i,'universal_citation'] = ''
                
            # Get the text content
            full_text = content_div.get_text()
            
            # Safely split by 'Source. ' - handle case where it might not exist
            full_text=full_text.split('Added by Laws ')
            temp.loc[i,'statute_text'] = full_text[0]
            temp.loc[i,'statute_mods'] = 'Added by Laws ' + full_text[1]
            
            # Safely get citation
            citation_div = soup.find('div',class_='citation')
            if citation_div and citation_div.find('span'):
                temp.loc[i,'universal_citation'] = citation_div.find('span').get_text()
            else:
                temp.loc[i,'universal_citation'] = 'Citation not found'
            
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            temp.loc[i,'statute_text'] = f"Error: {e}"
            temp.loc[i,'statute_mods'] = ''
            temp.loc[i,'universal_citation'] = ''
            
temp.reset_index(inplace=True)
main_df=pd.concat([main_df,temp],ignore_index=True)
main_df.to_csv('current_text_v1.csv',index=False)

# %%Oregon.
stat_split['oregon']='-'
s='oregon'
state_slug='oregon'
# Oregon uses volumes rather than years in URL; volume inferred from title
# For Title 128 in examples, volume-03
temp_df=current_df.loc[current_df.state==s]
print(np.sum(temp_df['MULTI']=='CHECK §§'))
print(temp_df.loc[temp_df.temp_statute=='nan','backsources_2023'])

# Split and normalize tokens; handle inputs like '§ 128.821' or '128-821'
_or_raw = temp_df['temp_statute'].astype('str').str.lower()
_or_tokens = _or_raw.str.findall(r'\d+')
temp = pd.DataFrame()
temp['state']=s
temp['chapter']=_or_tokens.apply(lambda t: t[0] if isinstance(t, list) and len(t)>=2 else '')
temp['section']=_or_tokens.apply(lambda t: '-'.join(t[1:]) if isinstance(t, list) and len(t)>=2 else '')
temp=temp[['state','chapter','section']]

# Paragraph if any
temp['paragraph']=temp['section'].str.extract(r'\((.*)',expand=True)
temp['paragraph']='('+temp['paragraph']
temp['section']=temp['section'].str.split('(',expand=True)[0]

# Section URL
temp['chapter']=temp['chapter'].astype(str).str.replace(r'\D+', '', regex=True)
temp['section']=temp['section'].astype(str).str.replace(r'[^0-9\-]+','', regex=True).str.replace(r'-+', '-', regex=True).str.strip('-')
temp['section_url']=(temp['chapter'].str.strip()+'-'+temp['section'].str.strip()).str.replace(r'-+', '-', regex=True).str.strip('-')

# Drop rows missing chapter or section after normalization
temp=temp[(temp['chapter']!='') & (temp['section']!='')]

# Volume inference:
# - Chapters <= 99 -> volume-02 (e.g., chapter 65)
# - Chapters >= 100 -> volume-03 (e.g., chapter 128)
def _or_volume(ch):
    try:
        c = int(str(ch))
        return 'volume-02' if c <= 99 else 'volume-03'
    except Exception:
        return 'volume-02'
temp['volume']=temp['chapter'].apply(_or_volume)
temp=temp.applymap(lambda x: x.lower() if isinstance(x, str) else x)

# Build URL per pattern:
# https://law.justia.com/codes/oregon/volume-03/chapter-128/section-128-821/
temp['chapter_padded']=temp['chapter'].str.zfill(3)
temp['url']=(
    temp['volume']+'/'
    +'chapter-'+temp['chapter_padded']+'/'
    +'section-'+temp['section_url']+'/'
)
temp['url']=url_base+state_slug+'/' + temp['url']

# Override: collapse OR sections 128-640-1 and 128-640-2 to section-128-640
_or_collapse_128_640 = temp['section_url'].isin(['128-640-1','128-640-2'])
if _or_collapse_128_640.any():
    temp.loc[_or_collapse_128_640, 'url'] = url_base + 'oregon/volume-03/chapter-128/section-128-640/'

# Ensure output columns
for _col in ['statute_text','statute_mods','universal_citation']:
    if _col not in temp.columns:
        temp[_col]=''

# Get statute text
for i in temp.index:
    url=temp.loc[i,'url']
    if not isinstance(url,str) or url.strip()=='' or 'volume' not in url:
        continue
    print(f"Fetching (OR): {url}")
    try:
        req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
        page = urlopen(req)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")

        content_div=soup.find('div',id='codes-content')
        if content_div:
            text_content=content_div.get_text()
            # Prefer trailing bracketed history/mod notes at end of OR statutes
            bracket=re.search(r'(\[[^\]]+\])\s*$', text_content, re.DOTALL)
            if bracket:
                statute_text=text_content[:bracket.start()].strip()
                statute_mods=bracket.group(1).strip()
            else:
                # Fallback: split at common OR markers
                patterns=[r'Note', r'Notes', r'Annotations', r'History']
                split_pos=len(text_content)
                for pat in patterns:
                    m=re.search(pat, text_content)
                    if m and m.start()<split_pos:
                        split_pos=m.start()
                statute_text=text_content[:split_pos].strip()
                statute_mods=text_content[split_pos:].strip() if split_pos<len(text_content) else ''
            temp.loc[i,'statute_text']=statute_text
            temp.loc[i,'statute_mods']=statute_mods
        else:
            temp.loc[i,'statute_text']='No content found'
            temp.loc[i,'statute_mods']=''

        cit_div=soup.find('div', class_='citation')
        if cit_div and cit_div.find('span'):
            temp.loc[i,'universal_citation']=cit_div.find('span').get_text()
        else:
            temp.loc[i,'universal_citation']=''
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        temp.loc[i,'statute_text']=f'Error: {e}'
        temp.loc[i,'statute_mods']=''
        temp.loc[i,'universal_citation']=''

temp.reset_index(inplace=True)
main_df=pd.concat([main_df,temp],ignore_index=True)
main_df.to_csv('current_text_v1.csv',index=False)


# %%Pennsylvania. Can't scrape the statutes because they are all saved in a PDF, not in Justia website.
stat_split['pennsylvania']='-'
s='pennsylvania'
state_slug='pennsylvania'
url_state_year=state_slug+'/2023/'
temp_df=current_df.loc[current_df.state==s]
print(np.sum(temp_df['MULTI']=='CHECK §§'))
print(temp_df.loc[temp_df.temp_statute=='nan','backsources_2023'])

# Normalize statute string and tokenize numbers (handles 7740.3, 20-77-7740-3, etc.)
_raw = temp_df['temp_statute'].astype('str').str.lower().str.replace(':','-', regex=False).str.replace('\u2013','-', regex=False).str.replace('\u2014','-', regex=False)
_raw = _raw.str.replace('.', '-', regex=False)
_tokens = _raw.str.findall(r'\d+')

temp = pd.DataFrame()
temp['state']=s

# Prefer Title/Chapter from backsources when available
_title_bs = temp_df['backsources_2023'].astype('str').str.extract(r'(?i)title\s+(\d+)', expand=False)
_chapter_bs = temp_df['backsources_2023'].astype('str').str.extract(r'(?i)chapter\s+(\d+)', expand=False)

def _pa_title(tok, tbs):
    if isinstance(tbs, str) and tbs:
        return tbs
    if isinstance(tok, list) and len(tok) >= 3:
        return tok[0]
    return ''

def _pa_chapter(tok, cbs, title_val):
    if isinstance(cbs, str) and cbs:
        return cbs
    if isinstance(tok, list):
        if len(tok) >= 3:
            return tok[1]
        if len(tok) == 2 and title_val:
            return tok[0]
    return ''

def _pa_section_path(tok, title_val, chap_val):
    if isinstance(tok, list):
        if len(tok) >= 3:
            return '-'.join(tok[2:])
        if len(tok) == 2:
            return tok[1]
    return ''

temp['tokens'] = _tokens
temp['title'] = [ _pa_title(t, tb) for t,tb in zip(temp['tokens'], _title_bs.fillna('')) ]
temp['chapter'] = [ _pa_chapter(t, cb, tv) for t,cb,tv in zip(temp['tokens'], _chapter_bs.fillna(''), temp['title']) ]
temp['section_path'] = [ _pa_section_path(t, tv, cv) for t,tv,cv in zip(temp['tokens'], temp['title'], temp['chapter']) ]

# Basic validation and normalization
temp['title'] = temp['title'].astype(str).str.replace(r'\D+', '', regex=True)
temp['chapter'] = temp['chapter'].astype(str).str.replace(r'\D+', '', regex=True)
temp['section_path'] = temp['section_path'].astype(str).str.replace(r'[^0-9\-]+','', regex=True).str.replace(r'-+', '-', regex=True).str.strip('-')

# Keep only rows with all parts
temp=temp[(temp['title']!='') & (temp['chapter']!='') & (temp['section_path']!='')]

# Derive section_url for reference
temp['section_url']=temp['section_path']

# Ensure output columns exist
for _col in ['statute_text','statute_mods','universal_citation']:
    if _col not in temp.columns:
        temp[_col]=''

# Normalize strings
temp=temp.applymap(lambda x: x.lower() if isinstance(x, str) else x)

# Build URL per pattern:
# https://law.justia.com/codes/pennsylvania/2023/title-20/chapter-77/section-7740-3/
temp['url']=(
    'title-'+temp['title']+'/'
    +'chapter-'+temp['chapter']+'/'
    +'section-'+temp['section_path']+'/'
)
temp['url']=url_base+url_state_year+temp['url']

# Fetch statute text
for i in temp.index:
    url=temp.loc[i,'url']
    if not isinstance(url,str) or url.strip()=='':
        continue
    print(f"Fetching (PA): {url}")
    try:
        req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
        page = urlopen(req)
        html = page.read().decode('utf-8')
        soup = BeautifulSoup(html, 'html.parser')

        content_div=soup.find('div', id='codes-content')
        if content_div:
            text_content=content_div.get_text()
            # Split at common PA markers
            patterns=[r'History', r'Cross References', r'Effective Date', r'Notes']
            split_pos=len(text_content)
            for pat in patterns:
                m=re.search(pat, text_content)
                if m and m.start()<split_pos:
                    split_pos=m.start()
            statute_text=text_content[:split_pos].strip()
            statute_mods=text_content[split_pos:].strip() if split_pos<len(text_content) else ''
            temp.loc[i,'statute_text']=statute_text
            temp.loc[i,'statute_mods']=statute_mods
        else:
            temp.loc[i,'statute_text']='No content found'
            temp.loc[i,'statute_mods']=''

        cit_div=soup.find('div', class_='citation')
        if cit_div and cit_div.find('span'):
            temp.loc[i,'universal_citation']=cit_div.find('span').get_text()
        else:
            temp.loc[i,'universal_citation']=''
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        temp.loc[i,'statute_text']=f'Error: {e}'
        temp.loc[i,'statute_mods']=''
        temp.loc[i,'universal_citation']=''

temp.reset_index(inplace=True)
main_df=pd.concat([main_df,temp],ignore_index=True)
main_df.to_csv('current_text_v1.csv',index=False)

# %%Rhode Island.
stat_split['rhode island']='-'
s='rhode island'
state_slug='rhode-island'
url_state_year=state_slug+'/2023/'
temp_df=current_df.loc[current_df.state==s]
print(np.sum(temp_df['MULTI']=='CHECK §§'))
print(temp_df.loc[temp_df.temp_statute=='nan','backsources_2023'])

# Normalize statute string and extract numeric tokens
_raw = temp_df['temp_statute'].astype('str').str.lower().str.replace(':','-', regex=False).str.replace('\u2013','-', regex=False).str.replace('\u2014','-', regex=False)
_raw = _raw.str.replace('\.', '-', regex=False)
_tokens = _raw.str.findall(r'\d+')

temp = pd.DataFrame()
temp['state']=s
temp['temp_statute']=_raw

# Derive title, chapter path, and section path
temp['title']=_tokens.apply(lambda t: t[0] if isinstance(t, list) and len(t)>0 else '')
temp['section_tokens']=_tokens
# Compute chapter tokens with special handling for Title 5, 53-1 family
def _ri_compute_chapter_tokens(tok_list):
    if isinstance(tok_list, list):
        if len(tok_list) >= 4 and tok_list[0] == '5' and tok_list[1] == '53' and tok_list[2] == '1':
            return tok_list[:3]
        return tok_list[:-1] if len(tok_list) > 1 else tok_list
    return []
temp['chapter_tokens']=temp['section_tokens'].apply(_ri_compute_chapter_tokens)
temp['chapter_path']=temp['chapter_tokens'].apply(lambda t: '-'.join(t) if isinstance(t, list) else '')
temp['section_path']=temp['section_tokens'].apply(lambda t: '-'.join(t) if isinstance(t, list) else '')

# Map to named columns
temp['chapter']=temp['chapter_tokens'].apply(lambda t: t[1] if isinstance(t, list) and len(t)>1 else '')
temp['section']=temp['section_tokens'].apply(lambda t: t[-1] if isinstance(t, list) and len(t)>0 else '')

# Sanity: ensure title is the first segment of section_path; fix chapter_path prefix if needed
temp['title_first'] = temp['section_path'].str.split('-', n=1).str[0]
_title_mismatch = temp['title'] != temp['title_first']
temp.loc[_title_mismatch, 'title'] = temp.loc[_title_mismatch, 'title_first']
temp['chapter_path'] = temp.apply(
    lambda r: r['chapter_path'] if str(r['chapter_path']).startswith(str(r['title'])+'-') else (str(r['title'])+'-'+str(r['chapter_path'])),
    axis=1
)
temp.drop(columns=['title_first'], inplace=True)

# Targeted RI fix: if section_path is 5-53-1-<x>-<y>, set chapter_path to 5-53-1
_ri_ch_fix = temp['section_path'].str.match(r'^5-53-1-\d+-\d+$')
temp.loc[_ri_ch_fix, 'chapter_path'] = '5-53-1'

# Targeted RI fix: chapters under 53-1-* belong to Title 5
_ri_53_1 = temp['chapter_path'].str.startswith('53-1')
temp.loc[_ri_53_1, 'title'] = '5'
temp.loc[_ri_53_1 & (~temp['chapter_path'].str.startswith('5-')), 'chapter_path'] = '5-' + temp.loc[_ri_53_1 & (~temp['chapter_path'].str.startswith('5-')), 'chapter_path']
temp.loc[_ri_53_1 & (~temp['section_path'].str.startswith('5-')), 'section_path'] = '5-' + temp.loc[_ri_53_1 & (~temp['section_path'].str.startswith('5-')), 'section_path']

# If backsources specifies Title N, prefer it and ensure paths are prefixed by N-
_title_from_bs = temp_df['backsources_2023'].astype('str').str.extract(r'(?i)title\s+(\d+)', expand=False).fillna('')
temp['title_from_bs'] = _title_from_bs
def _ensure_prefix(row):
    t = row.get('title_from_bs','')
    if t and not str(row['chapter_path']).startswith(t+'-'):
        row['chapter_path'] = t + '-' + str(row['chapter_path'])
    if t and not str(row['section_path']).startswith(t+'-'):
        row['section_path'] = t + '-' + str(row['section_path'])
    if t:
        row['title'] = t
    return row
temp = temp.apply(_ensure_prefix, axis=1)
temp.drop(columns=['title_from_bs'], inplace=True)

# Paragraph if present
temp['paragraph']=temp['temp_statute'].str.extract(r'\((.*)', expand=True)
temp['paragraph']='('+temp['paragraph']

# URL-friendly section
temp['section_url']=temp['section_path']

# Ensure output columns
for _col in ['statute_text','statute_mods','universal_citation']:
    temp[_col]=''

# Keep only valid rows
temp=temp[(temp['title']!='') & (temp['chapter_path']!='') & (temp['section_path']!='')]
temp=temp.applymap(lambda x: x.lower() if isinstance(x, str) else x)

# Build URL:
# https://law.justia.com/codes/rhode-island/2023/title-5/chapter-5-53-1/section-5-53-1-4/
# Force RI chapter depth for Title 5, 53-1 family: chapter must be exactly '5-53-1'
temp['chapter_path']=temp['chapter_path'].str.replace(r'^5-53-1-\d+$', '5-53-1', regex=True)
temp['url']=(
    'title-'+temp['title']+'/'
    +'chapter-'+temp['chapter_path']+'/'
    +'section-'+temp['section_path']+'/'
)
# Use 2023 for all RI URLs per user request
temp['url']=url_base+state_slug+'/2023/' + temp['url']

# Override URLs for RI Title 5, chapter 5-53-1, sections 5-53-1-3-*
_ri_5531_3_mask = temp['section_path'].str.match(r'^5-53-1-3-\d+$')
if _ri_5531_3_mask.any():
    temp.loc[_ri_5531_3_mask, 'url'] = (
        url_base+state_slug+'/2023/'
        +'title-5/chapter-5-53-1/section-5-53-1-3/'
    )

# Fetch statute text
for i in temp.index:
    url=temp.loc[i,'url']
    if not isinstance(url,str) or url.strip()=='':
        continue
    print(f"Fetching (RI): {url}")
    try:
        req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
        page = urlopen(req)
        html = page.read().decode('utf-8')
        soup = BeautifulSoup(html, 'html.parser')

        content_div=soup.find('div', id='codes-content')
        if content_div:
            text_content=content_div.get_text()
            # Split at common RI markers
            patterns=[r'History', r'History of Section', r'Compiler\'s Notes', r'Amendments']
            split_pos=len(text_content)
            for pat in patterns:
                m=re.search(pat, text_content)
                if m and m.start()<split_pos:
                    split_pos=m.start()
            statute_text=text_content[:split_pos].strip()
            statute_mods=text_content[split_pos:].strip() if split_pos<len(text_content) else ''
            temp.loc[i,'statute_text']=statute_text
            temp.loc[i,'statute_mods']=statute_mods
        else:
            temp.loc[i,'statute_text']='No content found'
            temp.loc[i,'statute_mods']=''

        cit_div=soup.find('div', class_='citation')
        if cit_div and cit_div.find('span'):
            temp.loc[i,'universal_citation']=cit_div.find('span').get_text()
        else:
            temp.loc[i,'universal_citation']=''
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        temp.loc[i,'statute_text']=f'Error: {e}'
        temp.loc[i,'statute_mods']=''
        temp.loc[i,'universal_citation']=''

temp.reset_index(inplace=True)
main_df=pd.concat([main_df,temp],ignore_index=True)
main_df.to_csv('current_text_v1.csv',index=False)

# %%South Carolina.
stat_split['south carolina']='-'
s='south carolina'
state_slug='south-carolina'
url_state_year=state_slug+'/2023/'
temp_df=current_df.loc[current_df.state==s]
print(np.sum(temp_df['MULTI']=='CHECK §§'))
print(temp_df.loc[temp_df.temp_statute=='nan','backsources_2023'])

# Split statute like 33-56-70 -> title, chapter, section
temp=temp_df['temp_statute'].astype('str').str.split('-',expand=True)
print(f"\nSouth Carolina split columns: {temp.shape[1]}")
if temp.shape[1] >= 3:
    temp.columns=['title','chapter','section'] + [f'extra_{i}' for i in range(temp.shape[1]-3)]
elif temp.shape[1] == 2:
    temp.columns=['title','chapter']
    temp['section']=''
else:
    temp.columns=['section']
    temp['title']=''
    temp['chapter']=''
temp['state']=s
temp=temp[['state','title','chapter','section']]

# Paragraph (if any)
temp['paragraph']=temp['section'].str.extract(r'\((.*)',expand=True)
temp['paragraph']='('+temp['paragraph']
temp['section']=temp['section'].str.split('(',expand=True)[0]

# Section URL
temp['section_url']=temp['title'].astype(str)+'-'+temp['chapter'].astype(str)+'-'+temp['section'].astype(str)
temp['section_url']=temp['section_url'].str.replace('.', '-', regex=False)
temp['section_url']=temp['section_url'].str.replace(r'[^0-9\-]+','', regex=True)

# Ensure output columns exist
for _col in ['statute_text','statute_mods','universal_citation']:
    if _col not in temp.columns:
        temp[_col]=''

# Normalize all strings to lower
temp=temp.applymap(lambda x: x.lower() if isinstance(x, str) else x)

# Build URL per pattern:
# https://law.justia.com/codes/south-carolina/2023/title-33/chapter-56/section-33-56-70/
temp['url']=(
    'title-'+temp['title']+'/'
    +'chapter-'+temp['chapter']+'/'
    +'section-'+temp['section_url']+'/'
)
temp['url']=url_base+url_state_year+temp['url']

# Get statute text
for i in temp.index:
    url=temp.loc[i,'url']
    if not isinstance(url,str) or url.strip()=='':
        continue
    print(f"Fetching (SC): {url}")
    try:
        req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
        page = urlopen(req)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")

        content_div=soup.find('div',id='codes-content')
        if content_div:
            text_content=content_div.get_text()
            # Split at amendment indicators common on SC pages
            patterns=[r'HISTORY', r'History', r"Editor's Note", r"Editor's Notes", r'Amendments']
            split_pos=len(text_content)
            for pat in patterns:
                m=re.search(pat, text_content)
                if m and m.start()<split_pos:
                    split_pos=m.start()
            statute_text=text_content[:split_pos].strip()
            statute_mods=text_content[split_pos:].strip() if split_pos<len(text_content) else ''
            temp.loc[i,'statute_text']=statute_text
            temp.loc[i,'statute_mods']=statute_mods
        else:
            temp.loc[i,'statute_text']='No content found'
            temp.loc[i,'statute_mods']=''

        cit_div=soup.find('div', class_='citation')
        if cit_div and cit_div.find('span'):
            temp.loc[i,'universal_citation']=cit_div.find('span').get_text()
        else:
            temp.loc[i,'universal_citation']=''
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        temp.loc[i,'statute_text']=f'Error: {e}'
        temp.loc[i,'statute_mods']=''
        temp.loc[i,'universal_citation']=''

temp.reset_index(inplace=True)
main_df=pd.concat([main_df,temp],ignore_index=True)
main_df.to_csv('current_text_v1.csv',index=False)

# %%South Dakota. One obs. has 37-30-36 as the section code, doesn't have info on statute text.
stat_split['south dakota']='-'
s='south dakota'
state_slug='south-dakota'
url_state_year=state_slug+'/2023/'
temp_df=current_df.loc[current_df.state==s]
print(np.sum(temp_df['MULTI']=='CHECK §§'))
print(temp_df.loc[temp_df.temp_statute=='nan','backsources_2023'])

# Split statute like 37-30-3 -> title, chapter, section
temp=temp_df['temp_statute'].astype('str').str.split('-',expand=True)
print(f"\nSouth Dakota split columns: {temp.shape[1]}")
if temp.shape[1] >= 3:
    temp.columns=['title','chapter','section'] + [f'extra_{i}' for i in range(temp.shape[1]-3)]
elif temp.shape[1] == 2:
    temp.columns=['title','chapter']
    temp['section']=''
else:
    temp.columns=['section']
    temp['title']=''
    temp['chapter']=''
temp['state']=s
temp=temp[['state','title','chapter','section']]

# Paragraph (if any)
temp['paragraph']=temp['section'].str.extract(r'\((.*)',expand=True)
temp['paragraph']='('+temp['paragraph']
temp['section']=temp['section'].str.split('(',expand=True)[0]
# Convert dotted section numbers (e.g., 6.1) to hyphenated form (6-1)
temp['section']=temp['section'].str.replace('.', '-', regex=False)

# Specific fixes: chapter '25a' should be '25' for 47-25-2, 47-25-10, 47-25-20
_sd_fix_sections = {'2','10','20'}
_sd_fix_mask = (
    temp['title'].astype(str).str.lower()=='47'
    ) & (
    temp['chapter'].astype(str).str.lower()=='25a'
    ) & (
    temp['section'].astype(str).str.replace(r'[^0-9]', '', regex=True).isin(_sd_fix_sections)
    )
temp.loc[_sd_fix_mask, 'chapter'] = '25'

# Section URL
temp['section_url']=temp['title'].astype(str)+'-'+temp['chapter'].astype(str)+'-'+temp['section'].astype(str)
temp['section_url']=temp['section_url'].str.replace(r'[^0-9\-]+','', regex=True)

# Ensure output columns exist
for _col in ['statute_text','statute_mods','universal_citation']:
    if _col not in temp.columns:
        temp[_col]=''

# Normalize all strings to lower
temp=temp.applymap(lambda x: x.lower() if isinstance(x, str) else x)

# Build URL per pattern:
# https://law.justia.com/codes/south-dakota/2023/title-37/chapter-30/section-37-30-3/
temp['url']=(
    'title-'+temp['title']+'/'
    +'chapter-'+temp['chapter']+'/'
    +'section-'+temp['section_url']+'/'
)
temp['url']=url_base+url_state_year+temp['url']

# Get statute text
for i in temp.index:
    url=temp.loc[i,'url']
    if not isinstance(url,str) or url.strip()=='':
        continue
    print(f"Fetching (SD): {url}")
    try:
        req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
        page = urlopen(req)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")

        content_div=soup.find('div',id='codes-content')
        if content_div:
            text_content=content_div.get_text()
            # Split at amendment indicators common on South Dakota pages
            patterns=[r'History', r'Source', r'Source:', r'Amended by', r'Repealed by', r'SL\s+\d{4}']
            split_pos=len(text_content)
            for pat in patterns:
                m=re.search(pat, text_content)
                if m and m.start()<split_pos:
                    split_pos=m.start()
            statute_text=text_content[:split_pos].strip()
            statute_mods=text_content[split_pos:].strip() if split_pos<len(text_content) else ''
            temp.loc[i,'statute_text']=statute_text
            temp.loc[i,'statute_mods']=statute_mods
        else:
            temp.loc[i,'statute_text']='No content found'
            temp.loc[i,'statute_mods']=''

        cit_div=soup.find('div', class_='citation')
        if cit_div and cit_div.find('span'):
            temp.loc[i,'universal_citation']=cit_div.find('span').get_text()
        else:
            temp.loc[i,'universal_citation']=''
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        temp.loc[i,'statute_text']=f'Error: {e}'
        temp.loc[i,'statute_mods']=''
        temp.loc[i,'universal_citation']=''

temp.reset_index(inplace=True)
main_df=pd.concat([main_df,temp],ignore_index=True)
main_df.to_csv('current_text_v1.csv',index=False)

# %%Tennessee.
stat_split['tennessee']='-'
s='tennessee'
url_state_year=s+'/2023/'
temp_df=current_df.loc[current_df.state==s]
print(np.sum(temp_df['MULTI']=='CHECK §§'))
print(temp_df.loc[temp_df.temp_statute=='nan','backsources_2023'])

# Split statute like 48-101-504
temp=temp_df['temp_statute'].astype('str').str.split('-', expand=True)
print(f"\nTennessee split columns: {temp.shape[1]}")
if temp.shape[1] >= 3:
    temp.columns=['title','chapter','section'] + [f'extra_{i}' for i in range(temp.shape[1]-3)]
elif temp.shape[1] == 2:
    temp.columns=['title','chapter']
    temp['section']=''
else:
    temp.columns=['section']
    temp['title']=''
    temp['chapter']=''
temp['state']=s
temp=temp[['state','title','chapter','section']]

# Paragraph (if any)
temp['paragraph']=temp['section'].str.extract(r'\((.*)',expand=True)
temp['paragraph']='('+temp['paragraph']
temp['section']=temp['section'].str.split('(',expand=True)[0]

# Section URL and part
temp['section_url']=temp['title'].astype(str)+'-'+temp['chapter'].astype(str)+'-'+temp['section'].astype(str)
# Strip any stray non-digit/hyphen characters from section_url
temp['section_url']=temp['section_url'].str.replace(r'[^0-9\-]+','', regex=True)
_secnum = pd.to_numeric(temp['section'].str.extract(r'(\d+)', expand=False), errors='coerce')
_partnum = (_secnum // 100).astype('Int64')
temp['part']=''
_idx = _partnum.notna() & (_partnum > 0)
temp.loc[_idx,'part']=_partnum[_idx].astype(int).astype(str)

# Slug for the title name (e.g., 'miscellaneous-corporation-provisions') from backsources_2023
_title_name = temp_df['backsources_2023'].astype(str).str.extract(r'(?i)title\s+\d+\s*(?:–|—|-|:)?\s*([^\n,;]+)', expand=False)
_title_slug = _title_name.fillna('').str.strip().str.lower()
_title_slug = _title_slug.str.replace(r'[^a-z0-9]+','-', regex=True).str.strip('-')
temp['title_slug']=_title_slug

# Fallback: known Tennessee title slugs by title/chapter when backsources lack a descriptive title
_tn_slug_fallback = pd.Series('', index=temp.index)
_tn_slug_fallback.loc[(temp['title']=='48') & (temp['chapter']=='101')] = 'miscellaneous-corporation-provisions'
_tn_slug_fallback.loc[(temp['title']=='48') & (temp['chapter']=='64')] = 'nonprofit-corporations'
_tn_slug_fallback.loc[(temp['title']=='48') & (temp['chapter']=='68')] = 'nonprofit-corporations'
_tn_slug_fallback.loc[(temp['title']=='48') & (temp['chapter']=='61')] = 'nonprofit-corporations'
_tn_slug_fallback.loc[(temp['title']=='48') & (temp['chapter']=='60')] = 'nonprofit-corporations'
_tn_slug_fallback.loc[(temp['title']=='48') & (temp['chapter']=='62')] = 'nonprofit-corporations'
temp['title_slug'] = temp['title_slug'].where(temp['title_slug']!='', _tn_slug_fallback)

# Normalize all strings to lower
temp=temp.applymap(lambda x: x.lower() if isinstance(x, str) else x)

# Build URL per pattern:
# https://law.justia.com/codes/tennessee/2023/title-48/miscellaneous-corporation-provisions/chapter-101/part-5/section-48-101-504/
temp['part_segment']=''
# Include part segment only when part > 1 by default
_tn_has_part = (temp['part'].astype(str).str.strip()!='') & (temp['part'].astype(str).str.strip()!='1')
temp.loc[_tn_has_part,'part_segment']='part-'+temp.loc[_tn_has_part,'part']+'/'
# Special case: Title 48 Chapter 60 requires part-1 in URL (e.g., 48-60-105)
_tn_force_part1 = (temp['title']=='48') & (temp['chapter']=='60') & (temp['part'].astype(str).str.strip().isin(['','1']))
temp.loc[_tn_force_part1,'part_segment']='part-1/'
# Special cases: Title 48 Chapter 64, sections 103 and 104 require part-1
_tn_force_part1_ch64 = (
    (temp['title']=='48') & (temp['chapter']=='64') &
    (temp['section'].astype(str).str.strip().isin(['103','104']))
)
temp.loc[_tn_force_part1_ch64,'part_segment']='part-1/'
temp['title_slug_segment']=''
temp.loc[temp['title_slug']!='','title_slug_segment']=temp['title_slug']+'/'
temp['url_with_part']=(
    'title-'+temp['title']+'/'
    +temp['title_slug_segment']
    +'chapter-'+temp['chapter']+'/'
    +temp['part_segment']
    +'section-'+temp['section_url']+'/'
)
temp['url_no_part']=(
    'title-'+temp['title']+'/'
    +temp['title_slug_segment']
    +'chapter-'+temp['chapter']+'/'
    +'section-'+temp['section_url']+'/'
)
temp['url'] = temp['url_with_part']
temp.loc[temp['part_segment']=='','url'] = temp.loc[temp['part_segment']=='','url_no_part']
temp['url']=url_base+url_state_year+temp['url']
# Safety: remove any stray parentheses from the final URL
temp['url']=temp['url'].str.replace(')', '', regex=False).str.replace('(', '', regex=False)

# Fetch statute text
for i in temp.index:
    url=temp.loc[i,'url']
    # For Tennessee, allow fetch even if title_slug is empty for Title 29 (no descriptive segment)
    _tn_title = temp.loc[i,'title'] if 'title' in temp.columns else ''
    if not isinstance(url,str) or url.strip()=='' or (temp.loc[i,'title_slug']=='' and _tn_title!='29'):
        continue
    print(f"Fetching (TN): {url}")
    try:
        req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
        page = urlopen(req)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")

        content_div=soup.find('div',id='codes-content')
        if content_div:
            text_content=content_div.get_text()
            # Special-case parsing for TN Title 29, Chapter 35, Section 102
            if (_tn_title=='29' and str(temp.loc[i,'chapter'])=='35' and str(temp.loc[i,'section'])=='102'):
                mods_match = re.search(r'(?:^|\n)Code\s+1858,', text_content)
                if mods_match:
                    split_pos = mods_match.start()
                else:
                    # fallback to generic patterns if specific anchor missing
                    split_pos=len(text_content)
                    for pat in [r'History', r'Amended by', r'Acts\s+\d{4}', r'Compiler\'s Notes']:
                        m=re.search(pat, text_content)
                        if m and m.start()<split_pos:
                            split_pos=m.start()
                statute_text=text_content[:split_pos].strip()
                statute_mods=text_content[split_pos:].strip() if split_pos<len(text_content) else ''
                temp.loc[i,'statute_text']=statute_text
                temp.loc[i,'statute_mods']=statute_mods
                # Force universal citation format for this case
                temp.loc[i,'universal_citation']='TN Code § 29-35-102 (2023)'
            else:
                # Split at amendment indicators common on TN pages
                patterns=[r'History', r'Amended by', r'Acts\s+\d{4}', r'Compiler\'s Notes']
                split_pos=len(text_content)
                for pat in patterns:
                    m=re.search(pat, text_content)
                    if m and m.start()<split_pos:
                        split_pos=m.start()
                statute_text=text_content[:split_pos].strip()
                statute_mods=text_content[split_pos:].strip() if split_pos<len(text_content) else ''
                temp.loc[i,'statute_text']=statute_text
                temp.loc[i,'statute_mods']=statute_mods
        else:
            temp.loc[i,'statute_text']='No content found'
            temp.loc[i,'statute_mods']=''

        cit_div=soup.find('div', class_='citation')
        if cit_div and cit_div.find('span'):
            temp.loc[i,'universal_citation']=cit_div.find('span').get_text()
        else:
            temp.loc[i,'universal_citation']=''
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        temp.loc[i,'statute_text']=f'Error: {e}'
        temp.loc[i,'statute_mods']=''
        temp.loc[i,'universal_citation']=''

temp.reset_index(inplace=True)
main_df=pd.concat([main_df,temp],ignore_index=True)
main_df.to_csv('current_text_v1.csv',index=False)

# %%Texas.
stat_split['texas']='.'  
s='texas'
url_state_year=s+'/2023/'
temp_df=current_df.loc[current_df.state==s]
print(np.sum(temp_df['MULTI']=='CHECK §§'))
print(temp_df.loc[temp_df.temp_statute=='nan','backsources_2023'])

temp=temp_df['temp_statute'].astype('str').str.split(stat_split[s],expand=True)
print(f"\nNumber of columns after split: {temp.shape[1]}")
if temp.shape[1]==2:
    temp.columns=['chapter','section_tail']
else:
    # fallback for unexpected splits
    temp.columns=['section_tail']
    temp['chapter']=np.nan
    temp=temp[['chapter','section_tail']]
temp['state']=s
temp['temp_statute']=temp_df['temp_statute'].astype('str')
temp['backsources_2023']=temp_df['backsources_2023'].astype('str')

# Parse statute parts like 303.052, 1803.053, 11.251 (keep any pre-split values from above)
_parts = temp['temp_statute'].str.extract(r'^(\d+)[\.:-]?(\d+)', expand=True)
# Clean chapter to keep only digits
_parts[0] = _parts[0].str.extract(r'(\d+)', expand=False)
temp['chapter'] = temp['chapter'].where(temp['chapter'].notna(), _parts[0])
temp['section_tail'] = temp['section_tail'].where(temp['section_tail'].notna(), _parts[1])
temp['paragraph']=temp['section_tail'].str.extract(r'(\(.*)$', expand=False)
temp['paragraph']=temp['paragraph'].apply(lambda v: '('+v if isinstance(v, str) and not v.startswith('(') else v)
temp['section_tail']=temp['section_tail'].str.split('(', expand=True)[0]
# Fix duplicated section tails like '059-059' -> '059'
temp['section_tail']=temp['section_tail'].str.replace(r'^(0*\d+)-\1$', r'\1', regex=True)

# URL-friendly section (e.g., 303-052)
temp['section_url']=(temp['chapter']+'-'+temp['section_tail']).str.replace(':','-', regex=False).str.rstrip()
temp['section'] = temp['chapter'].astype(str) + '.' + temp['section_tail'].astype(str)
# Normalize duplicates: '303-059-059' -> '303-059', '303.059.059' -> '303.059'
temp['section_url']=temp['section_url'].str.replace(r'^(\d+)-(0*\d+)-\2$', r'\1-\2', regex=True)
temp['section']=temp['section'].str.replace(r'^(\d+)\.(0*\d+)\.\2$', r'\1.\2', regex=True)

# Map code slug from backsources
_lower_src=temp['backsources_2023'].str.lower()
temp['code_slug']=''
# Common Texas codes on Justia
temp.loc[_lower_src.str.contains(r'business\s*&?\s*commerce\s*code'), 'code_slug']='business-and-commerce-code'
temp.loc[_lower_src.str.contains(r'business\s*organizations?\s*code'), 'code_slug']='business-organizations-code'
temp.loc[_lower_src.str.contains(r'\bbus\.?\s*&?\s*com\.?\s*code\b'), 'code_slug']='business-and-commerce-code'
temp.loc[_lower_src.str.contains(r'\bbus\.?\s*orgs?\.?\s*code\b'), 'code_slug']='business-organizations-code'
temp.loc[_lower_src.str.contains(r'occupations\s*code'), 'code_slug']='occupations-code'
temp.loc[_lower_src.str.contains(r'property\s*code'), 'code_slug']='property-code'
temp.loc[_lower_src.str.contains(r'health\s*-?\s*and\s*-?\s*safety\s*code'), 'code_slug']='health-and-safety-code'
temp.loc[_lower_src.str.contains(r'penal\s*code'), 'code_slug']='penal-code'
temp.loc[_lower_src.str.contains(r'family\s*code'), 'code_slug']='family-code'
temp.loc[_lower_src.str.contains(r'insurance\s*code'), 'code_slug']='insurance-code'
temp.loc[_lower_src.str.contains(r'government\s*code'), 'code_slug']='government-code'
temp.loc[_lower_src.str.contains(r'finance\s*code'), 'code_slug']='finance-code'
temp.loc[_lower_src.str.contains(r'civil\s*practice\s*and\s*remedies\s*code'), 'code_slug']='civil-practice-and-remedies-code'
temp.loc[_lower_src.str.contains(r'transportation\s*code'), 'code_slug']='transportation-code'
temp.loc[_lower_src.str.contains(r'labor\s*code'), 'code_slug']='labor-code'
temp.loc[_lower_src.str.contains(r'education\s*code'), 'code_slug']='education-code'
temp.loc[_lower_src.str.contains(r'utilit(?:y|ies)\s*code'), 'code_slug']='utilities-code'
temp.loc[_lower_src.str.contains(r'water\s*code'), 'code_slug']='water-code'
temp.loc[_lower_src.str.contains(r'agriculture\s*code'), 'code_slug']='agriculture-code'
temp.loc[_lower_src.str.contains(r'election\s*code'), 'code_slug']='election-code'
temp.loc[_lower_src.str.contains(r'local\s*government\s*code'), 'code_slug']='local-government-code'
temp.loc[_lower_src.str.contains(r'natural\s*resources\s*code'), 'code_slug']='natural-resources-code'
temp.loc[_lower_src.str.contains(r'tax\s*code'), 'code_slug']='tax-code'
temp.loc[_lower_src.str.contains(r'estates\s*code'), 'code_slug']='estates-code'

# Extract Title / Subtitle / Chapter / Subchapter from backsources when present
# Broad single-pattern extraction tolerating punctuation and ordering
wide = temp['backsources_2023'].str.extract(
    r'(?is)title\s*[-:]?\s*(\d+)\b.*?'
    r'(?:subtitle\s*[-:]?\s*([A-Za-z0-9\-]+)\b)?\s*.*?'
    r'chapter\s*[-:]?\s*(\d+)\b.*?'
    r'(?:subchapter\s*[-:]?\s*([A-Za-z0-9\-]+)\b)?',
    expand=True
)
temp['title']=wide[0]
temp['subtitle']=wide[1]
# Prefer explicit chapter from backsources; otherwise keep earlier parsed chapter
_chap_from_src=wide[2]
temp['chapter']=temp['chapter'].where(_chap_from_src.isna(), _chap_from_src)
temp['subchapter']=wide[3]

# Fallbacks using abbreviated forms if still missing
mask_title_missing = temp['title'].isna() | (temp['title']=='')
abbr_title = temp['backsources_2023'].str.extract(r'(?i)tit\.?\s*(\d+)', expand=True)[0]
temp.loc[mask_title_missing, 'title'] = abbr_title[mask_title_missing]

mask_subtitle_missing = temp['subtitle'].isna() | (temp['subtitle']=='')
abbr_subtitle = temp['backsources_2023'].str.extract(r'(?i)subt\.?\s*([A-Za-z0-9\-]+)', expand=True)[0]
temp.loc[mask_subtitle_missing, 'subtitle'] = abbr_subtitle[mask_subtitle_missing]

mask_chap_missing = temp['chapter'].isna() | (temp['chapter']=='')
abbr_chap = temp['backsources_2023'].str.extract(r'(?i)ch\.?\s*(\d+)', expand=True)[0]
temp.loc[mask_chap_missing, 'chapter'] = abbr_chap[mask_chap_missing]

mask_subchap_missing = temp['subchapter'].isna() | (temp['subchapter']=='')
abbr_subchap = temp['backsources_2023'].str.extract(r'(?i)subch\.?\s*([A-Za-z0-9\-]+)', expand=True)[0]
temp.loc[mask_subchap_missing, 'subchapter'] = abbr_subchap[mask_subchap_missing]

# Independent extractions anywhere in backsources (order-agnostic)
title_any = temp['backsources_2023'].str.extract(r'(?i)title\s*[-:]?\s*(\d+)', expand=False)
subtitle_any = temp['backsources_2023'].str.extract(r'(?i)subtitle\s*[-:]?\s*([A-Za-z0-9\-]+)', expand=False)
chap_any = temp['backsources_2023'].str.extract(r'(?i)chapter\s*[-:]?\s*([0-9A-Za-z\-]+)', expand=False)
subchap_any = temp['backsources_2023'].str.extract(r'(?i)subchapter\s*[-:]?\s*([A-Za-z][A-Za-z0-9\-]*)', expand=False)

temp['title'] = temp['title'].where(temp['title'].notna() & (temp['title']!=''), title_any)
temp['subtitle'] = temp['subtitle'].where(temp['subtitle'].notna() & (temp['subtitle']!=''), subtitle_any)
temp['chapter'] = temp['chapter'].where(temp['chapter'].notna() & (temp['chapter']!=''), chap_any)
temp['subchapter'] = temp['subchapter'].where(temp['subchapter'].notna() & (temp['subchapter']!=''), subchap_any)

# Fallback subchapter mapping for known Texas sections when backsources lack subchapter
def infer_tx_subchapter(code_slug_value: str, chapter_value: str, section_tail_value: str) -> str:
    code = str(code_slug_value or '')
    try:
        ch = int(re.findall(r'\d+', str(chapter_value or ''))[0])
    except Exception:
        ch = None
    try:
        sec_tail_num = int(re.findall(r'\d+', str(section_tail_value or ''))[0])
    except Exception:
        sec_tail_num = None

    # Business Organizations Code Title 1
    if code == 'business-organizations-code':
        if ch == 11:
            if sec_tail_num in {251}:  # §11.251
                return 'f'
            if sec_tail_num in {302, 303}:  # §11.302, §11.303
                return 'g'
            if sec_tail_num in {105}:  # §11.105
                return 'c'
        if ch == 3 and sec_tail_num in {56}:  # §3.056
            return 'b'
        if ch == 10 and sec_tail_num in {7}:  # §10.007
            return 'a'

    # Occupations Code Title 11
    if code == 'occupations-code':
        if ch in {1803, 1804} and sec_tail_num in {53}:  # §1803.053, §1804.053
            return 'b'

    # Business and Commerce Code Title 10
    if code == 'business-and-commerce-code':
        if ch == 303 and sec_tail_num in {52}:  # §303.052
            return 'b'

    return ''

_missing_subchap = (temp['subchapter'].isna()) | (temp['subchapter']=='')
temp.loc[_missing_subchap, 'subchapter'] = temp.loc[_missing_subchap].apply(
    lambda r: infer_tx_subchapter(r.get('code_slug',''), r.get('chapter',''), r.get('section_tail','')), axis=1
)
# Diagnostics to trace drops
print(f"TX rows after build: {len(temp)}")
print(f"TX sample statutes: {temp['temp_statute'].head(3).tolist()}")
print(f"TX chapter sample: {temp['chapter'].head(3).tolist()}, section_tail sample: {temp['section_tail'].head(3).tolist()}")
print(f"TX code_slug non-empty: {(temp['code_slug']!='').sum()} of {len(temp)}")
print(f"TX title non-empty: {int((temp['title'].fillna('')!='').sum())}, chapter non-empty: {int((temp['chapter'].fillna('')!='').sum())}, section_url non-empty: {int((temp['section_url'].fillna('')!='').sum())}")

# Heuristic title fallback by code family when backsources lack Title
def infer_tx_title(code_slug_value: str, chapter_value: str) -> str:
    try:
        chapter_num = int(re.findall(r'\d+', str(chapter_value))[0])
    except Exception:
        return ''
    # Occupations Code: Chapters 1800s map to Title 11
    if code_slug_value == 'occupations-code' and 1800 <= chapter_num < 1900:
        return '11'
    # Business Organizations Code: early chapters map to Title 1
    if code_slug_value == 'business-organizations-code' and 1 <= chapter_num <= 12:
        return '1'
    # Business and Commerce Code: Chapter 303 lives in Title 10 (per sample)
    if code_slug_value == 'business-and-commerce-code' and chapter_num == 303:
        return '10'
    return ''

_missing_title_mask = (temp['title'].isna()) | (temp['title']=='')
temp.loc[_missing_title_mask, 'title'] = temp.loc[_missing_title_mask].apply(
    lambda r: infer_tx_title(r.get('code_slug',''), r.get('chapter','')), axis=1
)

# Keep only needed columns and normalize
temp=temp[['state','code_slug','title','subtitle','chapter','subchapter','section','section_url','paragraph']]
# Fill optional fields to avoid notna checks later
temp['title'] = temp['title'].fillna('')
temp['chapter'] = temp['chapter'].fillna('')
temp['subtitle'] = temp['subtitle'].fillna('')
temp['subchapter'] = temp['subchapter'].fillna('')
temp['section_url'] = temp['section_url'].fillna('')
temp=temp[(temp['section_url']!='') & (temp['section_url']!='nan')]
temp=temp.applymap(lambda x: x.lower() if isinstance(x, str) else x)

# Build URL:
# e.g., https://law.justia.com/codes/texas/2023/business-and-commerce-code/title-10/subtitle-a/chapter-303/subchapter-b/section-303-052/
temp['subtitle_segment']=''
temp['subtitle_segment'] = temp['subtitle'].astype(str).apply(lambda x: 'subtitle-' + x + '/' if x else '')

temp['subchapter_segment']=''
temp['subchapter_segment'] = temp['subchapter'].astype(str).apply(lambda x: 'subchapter-' + x + '/' if x else '')

# Build URL only for rows with enough metadata; retain others in temp
_eligible = (temp['code_slug']!='') & (temp['title']!='') & (temp['chapter']!='') & (temp['section_url']!='')
print(f"TX rows eligible for URL: {int(_eligible.sum())} of {len(temp)}")
temp['url']=''
temp.loc[_eligible,'url'] = (
    url_base + url_state_year
    + temp.loc[_eligible,'code_slug'].astype(str) + '/title-' + temp.loc[_eligible,'title'].astype(str) + '/'
    + temp.loc[_eligible,'subtitle_segment'].astype(str)
    + 'chapter-' + temp.loc[_eligible,'chapter'].astype(str) + '/'
    + temp.loc[_eligible,'subchapter_segment'].astype(str)
    + 'section-' + temp.loc[_eligible,'section_url'].astype(str) + '/'
)

# Manual URL overrides for specific Texas sections with missing URLs
_manual_urls = {
    '1804-104': 'https://law.justia.com/codes/texas/2023/occupations-code/title-11/chapter-1804/subchapter-c/section-1804-104/',
    '303-059': 'https://law.justia.com/codes/texas/2023/business-and-commerce-code/title-10/subtitle-a/chapter-303/subchapter-b/section-303-059/',
    '1803-053': 'https://law.justia.com/codes/texas/2023/occupations-code/title-11/chapter-1803/subchapter-b/section-1803-053/',
    '1804-151': 'https://law.justia.com/codes/texas/2023/occupations-code/title-11/chapter-1804/subchapter-d/section-1804-151/',
    '303-052': 'https://law.justia.com/codes/texas/2023/business-and-commerce-code/title-10/subtitle-a/chapter-303/subchapter-b/section-303-052/'
}
for _sec, _u in _manual_urls.items():
    _mask = temp['section_url'].astype(str)==_sec
    if _mask.any():
        temp.loc[_mask,'url'] = _u

# Get statute text (include manual URLs and fill only missing)
for i in temp.index:
    # Skip if already populated
    if ('statute_text' in temp.columns and isinstance(temp.loc[i].get('statute_text', ''), str) and temp.loc[i].get('statute_text', '').strip() not in ('', 'No content found')
        and isinstance(temp.loc[i].get('universal_citation', ''), str) and temp.loc[i].get('universal_citation', '').strip() != ''):
        continue

    url = temp.loc[i,'url'] if 'url' in temp.columns else ''
    # Only fetch when a valid http(s) URL is present
    if not isinstance(url, str) or url.strip()=='' or urlparse(url).scheme not in ('http','https'):
        continue
    print(f"Fetching: {url}")
    try:
        req=urllib.request.Request(url, headers={'User-Agent': user_agent})
        page=urlopen(req)
        html=page.read().decode("utf-8")
        soup=BeautifulSoup(html, "html.parser")

        content_div=soup.find('div', id='codes-content')
        if content_div:
            text_content=content_div.get_text()

            amended_match = re.search(r'Amended by:', text_content)
            if amended_match:
                split_pos = amended_match.start()
            else:
                amendment_patterns=[
                    r'Added by Acts', r'Amended by Acts', r'Renumbered by Acts',
                    r'Transferred by Acts', r'Acts\s+\d{4}'
                ]
                split_pos=len(text_content)
                for pat in amendment_patterns:
                    m=re.search(pat, text_content)
                    if m and m.start()<split_pos:
                        split_pos=m.start()

            statute_text=text_content[:split_pos].strip()
            statute_mods=text_content[split_pos:].strip() if split_pos<len(text_content) else ''

            temp.loc[i,'statute_text']=statute_text
            temp.loc[i,'statute_mods']=statute_mods

            cit_div=soup.find('div', class_='citation')
            if cit_div and cit_div.find('span'):
                temp.loc[i,'universal_citation']=cit_div.find('span').get_text()
            else:
                temp.loc[i,'universal_citation']=''
        else:
            temp.loc[i,'statute_text']='No content found'
            temp.loc[i,'statute_mods']=''
            temp.loc[i,'universal_citation']=''
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        temp.loc[i,'statute_text']=f'Error: {e}'
        temp.loc[i,'statute_mods']=''
        temp.loc[i,'universal_citation']=''

temp.reset_index(inplace=True)
if 'main_df' not in locals():
    main_df=pd.DataFrame()
main_df=pd.concat([main_df,temp], ignore_index=True)
main_df.to_csv('current_text_v1.csv', index=False)
# %%Utah.
stat_split['utah']='-'
s='utah'
url_state_year=s+'/2023/'
temp_df=current_df.loc[current_df.state==s]
print(np.sum(temp_df['MULTI']=='CHECK §§'))
print(temp_df.loc[temp_df.temp_statute=='nan','backsources_2023'])
temp=temp_df['temp_statute'].str.split('-',expand=True)
temp.columns=['title','chapter','section']
temp['state']=s
temp=temp[['state','title','chapter','section']]

temp['paragraph']=temp['section'].str.extract('\((.*)',expand=True)
temp['paragraph']='('+temp['paragraph']
temp['section']=temp['section'].str.split('(',expand=True)[0]
# For Utah, section_url should be just the section number, not the full statute
temp['section_url']=temp['section']
temp['section_url']=temp['section_url'].str.replace('.','-', regex=False)
temp['section_url']=temp['section_url'].str.replace(':','-', regex=False)
temp['section_url']=temp['section_url'].str.rstrip()
temp=temp.applymap(lambda x: x.lower() if isinstance(x, str) else x)

# Derive part from numeric section: e.g., 1410 -> part 14, 706 -> part 7
_secnum = pd.to_numeric(temp['section_url'].str.extract(r'(\d+)')[0], errors='coerce')
_partnum = (_secnum // 100).astype('Int64')
temp['part_segment'] = ''
idx = _partnum.notna() & (_partnum > 0)
temp.loc[idx, 'part_segment'] = 'part-' + _partnum[idx].astype(int).astype(str) + '/'

temp['url']='title-'+temp['title']+'/chapter-'+temp['chapter']+'/' + temp['part_segment'] + 'section-'+temp['section_url']+'/'
temp['url']=url_base+url_state_year+temp['url']

#Get statute text.
for i in temp.index:
    if pd.isnull(temp.loc[i,'section_url'])==False:
        try:
            url=temp.loc[i,'url']
            req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
            page = urlopen(req)
            html = page.read().decode("utf-8")
            soup = BeautifulSoup(html, "html.parser")
            
            # Get the main content
            content_div = soup.find('div', id='codes-content')
            if content_div:
                text_content = content_div.get_text()
                
                # Extract statute text and modifications using regex
                # Look for common amendment patterns in Utah statutes
                amendment_patterns = [
                    r'Amended by Chapter \d+',
                    r'Repealed by Chapter \d+',
                    r'Effective \d{4}-\d{2}-\d{2}',
                    r'(\d{4}, c\. \d+.*?)(?=\n\n|\n[A-Z]|$)',
                    r'(\d{4} General Session.*?)(?=\n\n|\n[A-Z]|$)'
                ]
                
                statute_text = text_content
                statute_mods = ""
                
                # Find the first occurrence of any amendment pattern
                first_amendment_pos = len(text_content)
                for pattern in amendment_patterns:
                    match = re.search(pattern, text_content, re.DOTALL)
                    if match and match.start() < first_amendment_pos:
                        first_amendment_pos = match.start()
                
                if first_amendment_pos < len(text_content):
                    # Split at the first amendment
                    statute_text = text_content[:first_amendment_pos].strip()
                    statute_mods = text_content[first_amendment_pos:].strip()
                else:
                    # No amendments found, use entire content as statute text
                    statute_text = text_content.strip()
                    statute_mods = ""
                
                temp.loc[i,'statute_text'] = statute_text
                temp.loc[i,'statute_mods'] = statute_mods
                
                # Get universal citation
                citation_div = soup.find('div', class_='citation')
                if citation_div:
                    citation_span = citation_div.find('span')
                    if citation_span:
                        temp.loc[i,'universal_citation'] = citation_span.get_text()
                    else:
                        # Fallback citation format
                        title = temp.loc[i,'title']
                        chapter = temp.loc[i,'chapter']
                        section = temp.loc[i,'section']
                        temp.loc[i,'universal_citation'] = f"UT Code § {title}-{chapter}-{section} (2023)"
                else:
                    # Fallback citation format
                    title = temp.loc[i,'title']
                    chapter = temp.loc[i,'chapter']
                    section = temp.loc[i,'section']
                    temp.loc[i,'universal_citation'] = f"UT Code § {title}-{chapter}-{section} (2023)"
                    
        except Exception as e:
            print(f"Error processing Utah statute {temp.loc[i,'section_url']}: {e}")
            temp.loc[i,'statute_text'] = f'Error: {str(e)}'
            temp.loc[i,'statute_mods'] = ''
            temp.loc[i,'universal_citation'] = ''

temp.reset_index(inplace=True)
main_df=pd.concat([main_df,temp],ignore_index=True)
main_df.to_csv('current_text_v1.csv',index=False)

# %%Virginia. Couln't scrape the statute_mods
stat_split['virginia']='§'  # Changed from '.' to '§' for Virginia
s='virginia'
url_state_year=s+'/'  # Fixed: removed '/2023/' for Virginia
temp_df=current_df.loc[current_df.state==s]
print(np.sum(temp_df['MULTI']=='CHECK §§'))
print(temp_df.loc[temp_df.temp_statute=='nan','backsources_2023'])

# Debug: Check if temp_df has data
print(f"\nVirginia temp_df shape: {temp_df.shape}")
if temp_df.empty:
    print("No Virginia statutes found in current_df!")
    print("Available states:", current_df['state'].unique())
    exit()

# Debug: Check what the actual statute data looks like
print("Sample Virginia statutes:")
print(temp_df['temp_statute'].head(10))

# Debug: Check if url_base is defined
print(f"\nurl_base value: {url_base if 'url_base' in locals() else 'NOT DEFINED'}")

# For Virginia, we need to parse the statute format differently
# Example: "57-61.2" should give us title=57, chapter=5, section=57-61-2
temp = pd.DataFrame()
temp['state'] = s
temp['temp_statute'] = temp_df['temp_statute']

# Parse Virginia statutes properly
def parse_virginia_statute(statute_str):
    if pd.isna(statute_str) or statute_str == 'nan':
        return '57', '5', '57-61-2', ''  # Default values
    
    # Remove any leading/trailing whitespace and common prefixes
    statute_str = str(statute_str).strip()
    if statute_str.startswith('§'):
        statute_str = statute_str[1:].strip()
    
    # Handle different Virginia statute formats
    # Examples: "64.2-759", "57-48", "2.2-507.1", "57-61.2", "13.1-911", "55-532", "57-60(A)(1)"
    
    # First, check if we have a decimal in the title (like 64.2, 2.2, 13.1)
    if '.' in statute_str:
        # Split by first dash to separate title from rest
        first_dash_pos = statute_str.find('-')
        if first_dash_pos != -1:
            title = statute_str[:first_dash_pos]
            remaining = statute_str[first_dash_pos + 1:]
            
            # For titles with decimals, determine chapter based on known patterns
            if title == '64.2':
                chapter = '7'  # From URL: title-64-2/chapter-7/section-64-2-759/
            elif title == '2.2':
                chapter = '5'  # From URL: title-2-2/chapter-5/section-2-2-507-1/
            elif title == '13.1':
                chapter = '10'  # From URL: title-13-1/chapter-10/section-13-1-911/
            else:
                chapter = '5'  # Default for other decimal titles
            
            # The section is the full statute string
            section = statute_str
        else:
            # No dash found, use default
            title = statute_str
            chapter = '5'
            section = statute_str
    else:
        # No decimal in title (like "57-48", "55-532")
        parts = statute_str.split('-')
        
        if len(parts) >= 2:
            title = parts[0]
            # For Virginia statutes without decimals, determine chapter based on title
            if title == '55':
                chapter = '30'  # From URL: title-55/chapter-30/section-55-532/
            elif title == '57':
                chapter = '5'   # From URL: title-57/chapter-5/section-57-48/
            else:
                chapter = '5'   # Default chapter for Virginia
            # The section is the full statute string
            section = statute_str
        else:
            # Fallback
            title = statute_str
            chapter = '5'
            section = statute_str
    
    # Extract paragraph if it exists (anything in parentheses)
    # Handle cases like "57-60(A)(1)" - extract the paragraph part
    paragraph_match = re.search(r'\(([^)]+)\)', statute_str)
    if paragraph_match:
        # Find all parenthetical content
        all_parentheses = re.findall(r'\([^)]+\)', statute_str)
        paragraph = ''.join(all_parentheses)
        # Remove paragraph from section for URL construction
        section = re.sub(r'\([^)]+\)', '', statute_str).strip()
    else:
        paragraph = ''
    
    return title, chapter, section, paragraph

# Apply the parsing function
parsed_stats = temp['temp_statute'].apply(parse_virginia_statute)
temp['title'] = [x[0] for x in parsed_stats]
temp['chapter'] = [x[1] for x in parsed_stats]
temp['section'] = [x[2] for x in parsed_stats]
temp['paragraph'] = [x[3] for x in parsed_stats]

# Create section_url for URL construction
# The section column now has parentheses removed for URL construction
temp['section_url'] = temp['section'].str.replace('.', '-').str.replace(':', '-').str.rstrip()

# Create title_url for URL construction (convert decimals to dashes)
temp['title_url'] = temp['title'].str.replace('.', '-')

# Debug: Show what we're getting from the parsing
print("\nAfter parsing Virginia statutes:")
print(temp[['title','chapter','section','paragraph']].head(10))

# Test the parsing function with the specific cases mentioned
test_cases = ['13.1-911', '55-532', '57-60(A)(1)', '64.2-759', '2.2-507.1', '57-48']
print("\nTesting parsing function with specific cases:")
for test_case in test_cases:
    title, chapter, section, paragraph = parse_virginia_statute(test_case)
    print(f"'{test_case}' -> Title: {title}, Chapter: {chapter}, Section: {section}, Paragraph: '{paragraph}'")

# Virginia URL pattern based on working URL:
# https://law.justia.com/codes/virginia/title-57/chapter-5/section-57-61-2/
# For titles with decimals: https://law.justia.com/codes/virginia/2019/title-64-2/chapter-7/section-64-2-759/
temp['url'] = 'title-' + temp['title_url'] + '/chapter-' + temp['chapter'] + '/section-' + temp['section_url'] + '/'
temp['url'] = url_base + url_state_year + temp['url']

# Debug: Print some URLs to verify they're correct
print("\nSample Virginia URLs:")
print(temp['url'].head(10))

# Debug: Check if URLs are being created
print(f"\nTotal URLs created: {len(temp['url'].dropna())}")
print(f"Empty URLs: {temp['url'].isna().sum()}")

# Get statute text
for i in temp.index:
    if temp.loc[i,'section_url'] != 'nan' and not pd.isna(temp.loc[i,'section_url']):
        url = temp.loc[i,'url']
        print(f"Fetching: {url}")
        
        try:
            req = urllib.request.Request(url, headers={'User-Agent': user_agent})
            page = urlopen(req)
            html = page.read().decode("utf-8")
            soup = BeautifulSoup(html, "html.parser")
            
            # Check if content exists
            content_div = soup.find('div', id='codes-content')
            if content_div is None:
                print(f"No content div found for {url}")
                temp.loc[i,'statute_text'] = "No content found"
                temp.loc[i,'statute_mods'] = ''
                temp.loc[i,'universal_citation'] = ''
                continue
            
            # Extract the main statute text (everything before the amendment history)
            # Look for the main content and separate it from amendments
            main_content = content_div.find('div', class_='codes-content')
            if main_content:
                # Get all text content
                text_content = main_content.get_text(separator=' ', strip=True)
                
                # Split by common amendment indicators
                amendment_indicators = ['History', 'Amendments', '2003, c.', 'Acts', 'Code']
                split_point = len(text_content)
                
                for indicator in amendment_indicators:
                    pos = text_content.find(indicator)
                    if pos != -1 and pos < split_point:
                        split_point = pos
                
                # Extract main statute text and amendments
                statute_text = text_content[:split_point].strip()
                amendments = text_content[split_point:].strip()
                
                temp.loc[i,'statute_text'] = statute_text
                temp.loc[i,'statute_mods'] = amendments
            else:
                # Fallback: get all text and try to separate
                text_content = content_div.get_text(separator=' ', strip=True)
                temp.loc[i,'statute_text'] = text_content
                temp.loc[i,'statute_mods'] = ''
            
            # Get the universal citation
            citation_div = soup.find('div', class_='citation')
            if citation_div and citation_div.find('span'):
                temp.loc[i,'universal_citation'] = citation_div.find('span').get_text()
            else:
                # Try alternative citation elements
                citation_elem = soup.find('span', class_='citation') or soup.find('div', class_='universal-citation')
                if citation_elem:
                    temp.loc[i,'universal_citation'] = citation_elem.get_text()
                else:
                    temp.loc[i,'universal_citation'] = 'Citation not found'
                
        except urllib.error.HTTPError as e:
            if e.code == 403:
                print(f"Access forbidden (403) for {url} - skipping")
                temp.loc[i,'statute_text'] = "Access forbidden (403) - skipped"
                temp.loc[i,'statute_mods'] = ''
                temp.loc[i,'universal_citation'] = ''
            elif e.code == 404:
                print(f"Not found (404) for {url} - URL structure might be wrong")
                temp.loc[i,'statute_text'] = f"Not found (404) - URL structure wrong"
                temp.loc[i,'statute_mods'] = ''
                temp.loc[i,'universal_citation'] = ''
            else:
                print(f"HTTP Error {e.code} for {url}: {e}")
                temp.loc[i,'statute_text'] = f"HTTP Error {e.code}"
                temp.loc[i,'statute_mods'] = ''
                temp.loc[i,'universal_citation'] = ''
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            temp.loc[i,'statute_text'] = f"Error: {e}"
            temp.loc[i,'statute_mods'] = ''
            temp.loc[i,'universal_citation'] = ''

temp.reset_index(inplace=True)
main_df = pd.concat([main_df, temp], ignore_index=True)
main_df.to_csv('current_text_v1.csv', index=False)

# %%Vermont.
stat_split['vermont']=' '  # Vermont uses '.' as delimiter
s='vermont'
url_state_year=s+'/2023/'
temp_df=current_df.loc[current_df.state==s]
print(np.sum(temp_df['MULTI']=='CHECK §§'))
print(temp_df.loc[temp_df.temp_statute=='nan','backsources_2023'])

temp=temp_df['temp_statute'].str.split(stat_split[s],expand=True)
print(f"\nNumber of columns after split: {temp.shape[1]}")
temp.columns=['section']
temp=temp[temp.section!='nan']
temp['title']=temp_df.backsources_2023.str.extract(r'tit. (\d+)',expand=False)
temp.loc[pd.isnull(temp.title)==True,'title']='11b'
temp.loc[temp.title=='11','title']='11b'
temp.loc[temp.title=='11b','section']=temp_df.backsources_2023.str.extract(r'§ (\d+\.\d+)',expand=False)

temp.loc[temp.title=='9','chapter']='63'
temp.loc[temp.title=='18','chapter']='221'
temp.loc[temp.title=='11b','chapter']=temp.section.str.extract(r'(\d+).',expand=False)

temp['state']=s
temp=temp[['state','title','chapter','section']]

temp['paragraph']=temp['section'].str.extract('\((.*)',expand=True)
temp['paragraph']='('+temp['paragraph']
temp['section']=temp['section'].str.split('(',expand=True)[0]
temp['section_url']=temp['section'].str.replace('.','-')
temp['section_url']=temp['section_url'].str.rstrip()
temp=temp.map(lambda x: x.lower() if isinstance(x, str) else x)  # Fixed deprecated applymap

# Vermont URL pattern based on working URL:
# https://law.justia.com/codes/vermont/2023/title-11b/chapter-12/section-12-02/
temp['url']='title-'+temp['title']+'/chapter-'+temp['chapter']+'/section-'+temp['section_url']+'/'
temp['url']=url_base+url_state_year+temp['url']

#Get statute text.
for i in temp.index:
    if temp.loc[i,'section_url']!='nan':
        url=temp.loc[i,'url']
        print(f"Fetching: {url}")
        req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
        page = urlopen(req)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        soup.find('div',id='codes-content').get_text()
    
        #This separates text into statute and previous amendments to statute.
        text=soup.find('div',id='codes-content')
        text=text.get_text().split('(Added ')
        temp.loc[i,'statute_text']=''.join(text[0])
        temp.loc[i,'statute_mods']='(Added '+''.join(text[1])
        
        #This gets the universal citation.
        temp.loc[i,'universal_citation']=soup.find('div',class_='citation').find('span').get_text()

temp.reset_index(inplace=True)
main_df=pd.concat([main_df,temp],ignore_index=True)
main_df.to_csv('current_text_v1.csv',index=False)

# %%Washington. Multi issue. The following URL is given as source for one statute https://www.sos.wa.gov/charities/Charitable-Organizations.aspx, and Yes is given for another. RCW 11.110 refers to an entire chapter.  Do WACs by hand. They are in an archive here: https://lawfilesext.leg.wa.gov/law/WACArchive/2023/WAC%20434%20-120%20%20CHAPTER.htm
stat_split['washington']='.'  # Washington uses '.' as delimiter
s='washington'
url_state_year=s+'/2023/'
temp_df=current_df.loc[current_df.state==s]
print(np.sum(temp_df['MULTI']=='CHECK §§'))

#Get missing statutes from backsources_2023.
temp_df.loc[((temp_df.temp_statute=='nan') & (temp_df.backsources_2023.str.contains('WAC'))),'temp_statute']=temp_df.backsources_2023.str.extract(r'WAC (\d+\-\d+\-+\d+)',expand=False)
temp_df.loc[((temp_df.temp_statute=='nan') & (temp_df.backsources_2023.str.contains('RCW'))),'temp_statute']=temp_df.backsources_2023.str.extract(r'RCW (\d+\.+\d+)',expand=False)
temp_df['temp_statute']=temp_df['temp_statute'].str.replace('-','.')

print(temp_df.loc[temp_df.temp_statute=='nan','backsources_2023'])
temp=temp_df['temp_statute'].str.split(stat_split[s],expand=True)
print(f"\nNumber of columns after split: {temp.shape[1]}")

temp.columns=['title','chapter','section']
temp['state']=s
temp=temp[['state','title','chapter','section']]

temp['paragraph']=temp['section'].str.extract('\((.*)',expand=True)
temp['paragraph']='('+temp['paragraph']
temp['section']=temp['section'].str.split('(',expand=True)[0]
temp['section_url']=temp_df['temp_statute'].str.split('(',expand=True)[0]
temp['section_url']=temp['section_url'].str.replace('.','-')
temp['section_url']=temp['section_url'].str.rstrip()
temp=temp.map(lambda x: x.lower() if isinstance(x, str) else x)

# Washington URL pattern based on working URL:
# https://law.justia.com/codes/washington/2023/title-19/chapter-19-09/section-19-09-075/
temp['url']='title-'+temp['title']+'/chapter-'+temp['title']+'-'+temp['chapter']+'/section-'+temp['section_url']+'/'
temp['url']=url_base+url_state_year+temp['url']
temp.loc[temp.section_url=='11-110','section_url']='nan'

#Get statute text.
for i in temp.index:
    if temp.loc[i,'section_url']!='nan':
        if temp.loc[i,'title']=='434':
            temp.loc[i,['statute_text','statute_mods','universal_citation']]=''
        else:
            url=temp.loc[i,'url']
            print(f"Fetching: {url}")
            req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
            page = urlopen(req)
            html = page.read().decode("utf-8")
            soup = BeautifulSoup(html, "html.parser")
            soup.find('div',id='codes-content').get_text()
        
            #This separates text into statute and previous amendments to statute.
            text=soup.find('div',id='codes-content')
            text=text.get_text().split('[ ')
            temp.loc[i,'statute_text']=''.join(text[0])
            temp.loc[i,'statute_mods']='[ '+''.join(text[1])
            
            #This gets the universal citation.
            temp.loc[i,'universal_citation']=soup.find('div',class_='citation').find('span').get_text()

temp.reset_index(inplace=True)
main_df=pd.concat([main_df,temp],ignore_index=True)
main_df.to_csv('current_text_v1.csv',index=False)

# %%Wisconsin. One obs. gives the following URL as a source http://www.wdfi.org/charitableorganizations/.
stat_split['wisconsin']='.' 
s='wisconsin'
url_state_year=s+'/2023/'
temp_df=current_df.loc[current_df.state==s]
print(np.sum(temp_df['MULTI']=='CHECK §§'))
print(temp_df.loc[temp_df.temp_statute=='nan','backsources_2023'])
temp=temp_df['temp_statute'].str.split(stat_split[s],expand=True)
print(f"\nNumber of columns after split: {temp.shape[1]}")

temp.columns=['chapter','section']
temp['state']=s
temp=temp[['state','chapter','section']]

temp['paragraph']=temp['section'].str.extract('\((.*)',expand=True)
temp['paragraph']='('+temp['paragraph']
temp['section']=temp['section'].str.split('(',expand=True)[0]
temp['section_url']=temp_df['temp_statute'].str.split('(',expand=True)[0]
temp['section_url']=temp['section_url'].str.replace('.','-')
temp['section_url']=temp['section_url'].str.rstrip()
temp=temp.map(lambda x: x.lower() if isinstance(x, str) else x)

# Wisconsin URL pattern based on working URL:
# https://law.justia.com/codes/wisconsin/2023/chapter-701/section-701-0706/
temp['url']='chapter-'+temp['chapter']+'/section-'+temp['section_url']+'/'
temp['url']=url_base+url_state_year+temp['url']

#Get statute text.
for i in temp.index:
    if temp.loc[i,'section_url']!='nan':
        url=temp.loc[i,'url']
        print(f"Fetching: {url}")
        req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
        page = urlopen(req)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        soup.find('div',id='codes-content').get_text()
    
        #This separates text into statute and previous amendments to statute.
        text=soup.find('div',id='codes-content')
        text=text.get_text().split('History: ')
        temp.loc[i,'statute_text']=''.join(text[0])
        temp.loc[i,'statute_mods']='History: '+''.join(text[1])
        
        #This gets the universal citation.
        temp.loc[i,'universal_citation']=soup.find('div',class_='citation').find('span').get_text()
temp.reset_index(inplace=True)
main_df=pd.concat([main_df,temp],ignore_index=True)
main_df.to_csv('current_text_v1.csv',index=False)

# %%West Virginia. Multi issue. Only some statutes have modifications.
stat_split['west virginia']='-'
s='west virginia'
url_state_year=s.replace(' ','-')+'/2023/'  
temp_df=current_df.loc[current_df.state==s]
print(np.sum(temp_df['MULTI']=='CHECK §§'))
temp=temp_df['temp_statute'].str.split(stat_split[s],expand=True)
temp.columns=['chapter','article','section']  
temp['state']=s
temp=temp[['state','chapter','article','section']]

temp['paragraph']=temp['section'].str.extract('\((.*)',expand=True)
temp['paragraph']='('+temp['paragraph']
temp['section']=temp['section'].str.split('(',expand=True)[0]
temp['section_url']=temp_df['temp_statute'].str.split('(',expand=True)[0]
temp['section_url']=temp['section_url'].str.replace('.','-')
temp['section_url']=temp['section_url'].str.rstrip()
temp=temp.map(lambda x: x.lower() if isinstance(x, str) else x)

# West Virginia URL pattern:
# https://law.justia.com/codes/west-virginia/2023/chapter-29/article-19/section-29-19-5/
temp['url']='chapter-'+temp['chapter']+'/article-'+temp['article']+'/section-'+temp['section_url']+'/'
temp['url']=url_base+url_state_year+temp['url']

#Get statute text.
for i in temp.index:
    if temp.loc[i,'section_url']!='nan':
        url=temp.loc[i,'url']
        print(f"Fetching: {url}")
        req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
        page = urlopen(req)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        soup.find('div',id='codes-content').get_text()
    
        #This separates text into statute and previous amendments to statute.
        text=soup.find('div',id='codes-content')
        if 'NOTE: ' in text.get_text():
            text=text.get_text(separator='</p><p>').split('</p><p>')
            temp.loc[i,'statute_text']=''.join(text[2:])
            temp.loc[i,'statute_mods']=''.join(text[1])
        else:
            text=text.get_text()
            temp.loc[i,'statute_text']=''.join(text)
            temp.loc[i,'statute_mods']=''
        
        #This gets the universal citation.
        temp.loc[i,'universal_citation']=soup.find('div',class_='citation').find('span').get_text()

temp.reset_index(inplace=True)
main_df=pd.concat([main_df,temp],ignore_index=True)
main_df.to_csv('current_text_v1.csv',index=False)

# %%Wyoming. One obs. has no information.
stat_split['wyoming']='-'
s='wyoming'
url_state_year=s.replace(' ','-')+'/2023/'
temp_df=current_df.loc[current_df.state==s]
print(np.sum(temp_df['MULTI']=='CHECK §§'))
print(temp_df.loc[temp_df.temp_statute=='nan','backsources_2023'])

temp=temp_df['temp_statute'].str.split(stat_split[s],expand=True)
temp.columns=['title','chapter','section']  # Changed: first part is title, second is chapter
temp['state']=s

temp['article']=temp['section'].str.split('(',expand=True)[0]
temp.loc[(temp.section.str.len()==3),'article']=temp['section'].str[0]
temp.loc[(temp.section.str.len()==4),'article']=temp['section'].str[:2]

temp=temp[['state','title','chapter','article','section']]

temp['paragraph']=temp['section'].str.extract('\((.*)',expand=True)
temp['paragraph']='('+temp['paragraph']
temp['section']=temp['section'].str.split('(',expand=True)[0]
temp['section_url']=temp_df['temp_statute'].str.split('(',expand=True)[0]
temp['section_url']=temp['section_url'].str.replace('.','-')
temp['section_url']=temp['section_url'].str.rstrip()
temp=temp.map(lambda x: x.lower() if isinstance(x, str) else x)  # Fixed deprecated applymap

#Wyoming URL pattern based on working URL:
#https://law.justia.com/codes/wyoming/2023/title-17/chapter-19/article-11/section-17-19-1102/
#https://law.justia.com/codes/wyoming/2023/title-17/chapter-19/article-14/section-17-19-1420/
temp['url']='title-'+temp['title']+'/chapter-'+temp['chapter']+'/article-'+temp['article']+'/section-'+temp['section_url']+'/'
temp['url']=url_base+url_state_year+temp['url']

#Get statute text.
for i in temp.index:
    if temp.loc[i,'section_url']!='nan':
        url=temp.loc[i,'url']
        print(f"Fetching: {url}")
        req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
        page = urlopen(req)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        soup.find('div',id='codes-content').get_text()
    
        #This separates text into statute and previous amendments to statute.
        text=soup.find('div',id='codes-content')
        text=text.get_text()
        temp.loc[i,'statute_text']=''.join(text)
        temp.loc[i,'statute_mods']=''
        
        #This gets the universal citation.
        temp.loc[i,'universal_citation']=soup.find('div',class_='citation').find('span').get_text()

temp.reset_index(inplace=True)
main_df=pd.concat([main_df,temp],ignore_index=True)
main_df.to_csv('current_text_v1.csv',index=False)


# %%
