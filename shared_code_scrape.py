# -*- coding: utf-8 -*-
"""
Created on Thu Aug 21 17:57:57 2025

@author: dr636
"""

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
os.chdir('')

lc_df=pd.read_csv('',encoding='latin-1')
#Read in statute file if it exists.
x=0
if x==1:
    main_df=pd.read_csv('current_text_v1.csv')

#Create df for matched statutes.
current_df=lc_df.loc[lc_df.backsources_2019==lc_df.backsources_2023]
current_df=current_df.loc[((current_df.backsources_2019.isnull()==False) & (pd.isnull(current_df.backsources_2023)==False))]
current_df=current_df.loc[((current_df.backsources_2023!='No') & (current_df.backsources_2023!='NO'))]

# %%Scrape statutes.
current_df['temp_statute']=current_df['statute_section'].astype('str')
current_df['temp_statute']=current_df['temp_statute'].replace('{SS}: ','',regex=True)
current_df['state']=current_df.state.str.lower()

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
temp[['section','subsection']]=temp['section'].str.split('.',expand=True)
temp['paragraph']=temp['section'].str.extract('\((.*)',expand=True)
temp['paragraph']='('+temp['paragraph']
temp['section']=temp['section'].str.split('(',expand=True)[0]
temp['section_url']=temp_df['temp_statute'].str.split('(',expand=True)[0]
temp['section_url']=temp['section_url'].str.replace('.','-')
temp=temp.applymap(lambda x: x.lower() if isinstance(x, str) else x)
parts=temp['paragraph'].str.split("(", 2)
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
    page = urlopen(url)
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
parts=temp['paragraph'].str.split("(", 2)
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
    page = urlopen(url)
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
parts=temp['paragraph'].str.split("(", 2)
for i in temp.index:
    if pd.isna(temp.loc[i,'paragraph'])==False:
        if len(parts[i])==2:
            temp.loc[i,'subparagraph_1']='('+temp.loc[i,'paragraph'].split("(", 2)[1]
        elif len(parts[i])==3:
            temp.loc[i,'subparagraph_1']='('+temp.loc[i,'paragraph'].split("(", 2)[1]
            temp.loc[i,'subparagraph_2']='('+temp.loc[i,'paragraph'].split("(", 2)[2]

temp['part']=np.NaN
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
        page = urlopen(url)
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
parts=temp['paragraph'].str.split("(", 2)
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
        page = urlopen(url)
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
        page = urlopen(url)
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
parts=temp['paragraph'].str.split("(", 2)
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
        page = urlopen(url)
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
parts=temp['paragraph'].str.split("(", 2)
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
        page = urlopen(url)
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
parts=temp['paragraph'].str.split("(", 2)
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
        page = urlopen(url)
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
parts=temp['paragraph'].str.split("(", 2)
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
        page = urlopen(url)
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
        page = urlopen(url)
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
parts=temp['paragraph'].str.split("(", 2)
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
        page = urlopen(url)
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
        page = urlopen(url)
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
        page = urlopen(url)
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
        page = urlopen(url)
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
        page = urlopen(url)
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
        page = urlopen(url)
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
        page = urlopen(url)
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
        page = urlopen(url)
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
        page = urlopen(url)
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
        page = urlopen(url)
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
        page = urlopen(url)
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
        page = urlopen(url)
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
    if temp.loc[i,'section_url']!='nan':
        url=temp.loc[i,'url']
        page = urlopen(url)
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
        page = urlopen(url)
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
        page = urlopen(url)
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
        page = urlopen(url)
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
        page = urlopen(url)
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
        page = urlopen(url)
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

# %%Oklahoma.


# %%Oregon.


# %%Pennsylvania.


# %%Rhode Island.


# %%South Carolina.


# %%South Dakota.


# %%Tennessee.


# %%Texas.


# %%Utah.


# %%Virginia.


# %%Vermont.


# %%Washington.


# %%Wisconsin.


# %%West Virginia.


# %%Wyoming.
stat_split['wyoming']='-'
s='wyoming'
url_state_year=s.replace(' ','-')+'/2023/'
temp_df=current_df.loc[current_df.state==s]
print(np.sum(temp_df['MULTI']=='CHECK §§'))
print(temp_df.loc[temp_df.temp_statute=='nan','backsources_2023'])
temp=temp_df['temp_statute'].str.split(stat_split[s],expand=True)
temp.columns=['chapter','article','section']
temp['state']=s
temp=temp[['state','chapter','article','section']]

temp.loc[(temp.part.str.len()==3),'part']=temp['part'].str[0]
temp.loc[(temp.part.str.len()==4),'part']=temp['part'].str[:2]

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
        page = urlopen(url)
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













































stat_split['wyoming']='-'
s='wyoming'
url_state_year=s.replace(' ','-')+'/2023/'
temp_df=current_df.loc[current_df.state==s]
print(np.sum(temp_df['MULTI']=='CHECK §§'))
print(temp_df.loc[temp_df.temp_statute=='nan','backsources_2023'])
temp=temp_df['temp_statute'].str.split(stat_split[s],expand=True)
temp.columns=['chapter','article','section']
temp['state']=s
temp=temp[['state','chapter','article','section']]

temp.loc[(temp.part.str.len()==3),'part']=temp['part'].str[0]
temp.loc[(temp.part.str.len()==4),'part']=temp['part'].str[:2]

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
        page = urlopen(url)
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

