from email import message_from_string
from email.iterators import _structure

x = """Delivered-To: alexkiro.edw@gmail.com
Received: by 2002:a05:6022:4190:b0:51:9351:157d with SMTP id c16csp189386laa;
        Wed, 10 Apr 2024 00:02:27 -0700 (PDT)
X-Google-Smtp-Source: AGHT+IFKdy8nCnuYaczFeF3KcDjXR0jXz1PKhcCzNzc7PT09/oLXifpccQnhQmwMWRem/HcPcfIQ
X-Received: by 2002:a05:620a:460e:b0:78d:3438:85e3 with SMTP id br14-20020a05620a460e00b0078d343885e3mr2304228qkb.12.1712732547224;
        Wed, 10 Apr 2024 00:02:27 -0700 (PDT)
ARC-Seal: i=1; a=rsa-sha256; t=1712732547; cv=none;
        d=google.com; s=arc-20160816;
        b=X7mOi4OTPUGsxFr7LfiR38p31Yqp/I2Y/77Zlc+oqldsym2zzDVk7et26ZG7yEUYSC
         utmUm620SPpS3XLRtHToKL1LVZKeB44ux7QAWKwnQkhJjnJ0rXX5vKsw+qovCQlm2kS2
         3ZkJMrCobMe2m/nS0xadmdq41INsP7FIOwc4wQfT/2meZg3oEy+xl2Pmf94tnQlI3H/N
         Atpa4rSI3fx1konakh34cm53LeJqYl3snFIvY4dkqjrlFfsdHG8G1FQ5IqPGcSb4QTRl
         IVkjnyGys66ffHE7t79OqN8GekZvws6HHw8w0BPqnbmMgY5RBFSWsDiAMuYZSr5vxeLK
         IovA==
ARC-Message-Signature: i=1; a=rsa-sha256; c=relaxed/relaxed; d=google.com; s=arc-20160816;
        h=message-id:list-unsubscribe-post:list-unsubscribe:to:from:subject
         :mime-version:date:dkim-signature:dkim-signature;
        bh=UsYiM1Yfl4zaw8vLSwVotbL6uU83FtAGXKyd5jPctvw=;
        fh=tuxh70/aIlGvVMyw5bvn+6m8hDYjO0ukcn3qd2OspRg=;
        b=C72+60iG6/vgvRSQWCNbqIKKvnwtim5lq8fnDOdBOR9nloMnJtDMXZ6vNF2TQbDdSh
         ihGiWNQDNnkX4Gk/tfFz9lgM8bZ8EDys0xHY4K6Ep3veOWUcklzjlYJn1J72onfWMH81
         bKUDuExBFGocfWEUuWdGyxB41mbY/wpgBF4+RcYvTVilDmbO+jauSiTqQeNWbxXS/qDa
         rP/1tqH2y7WDH4sauLGnZ53zEHlE6lwg35GVhPL20Xyemlw1LeD9u/DJ/bwSYvNKtD7l
         Bm4xBaM+tPhQP1M1G+vkszqQz6mufz8jsdYK7/ZpJVojFo9y14KUv5RCBzTBsT4gStkK
         jQrg==;
        dara=google.com
ARC-Authentication-Results: i=1; mx.google.com;
       dkim=pass header.i=@cio90012.visily.ai header.s=mailo header.b=TsIvtLZJ;
       dkim=pass header.i=@mailgun.org header.s=mg header.b=AALhei2d;
       spf=pass (google.com: domain of postmaster@cio90012.visily.ai designates 159.112.241.114 as permitted sender) smtp.mailfrom=postmaster@cio90012.visily.ai;
       dmarc=pass (p=QUARANTINE sp=QUARANTINE dis=NONE) header.from=visily.ai
Return-Path: <postmaster@cio90012.visily.ai>
Received: from m241-114.mailgun.net (m241-114.mailgun.net. [159.112.241.114])
        by mx.google.com with UTF8SMTPS id i24-20020ae9ee18000000b0078bd1b249f2si11627189qkg.219.2024.04.10.00.02.27
        for <alexkiro.edw@gmail.com>
        (version=TLS1_3 cipher=TLS_AES_128_GCM_SHA256 bits=128/128);
        Wed, 10 Apr 2024 00:02:27 -0700 (PDT)
Received-SPF: pass (google.com: domain of postmaster@cio90012.visily.ai designates 159.112.241.114 as permitted sender) client-ip=159.112.241.114;
Authentication-Results: mx.google.com;
       dkim=pass header.i=@cio90012.visily.ai header.s=mailo header.b=TsIvtLZJ;
       dkim=pass header.i=@mailgun.org header.s=mg header.b=AALhei2d;
       spf=pass (google.com: domain of postmaster@cio90012.visily.ai designates 159.112.241.114 as permitted sender) smtp.mailfrom=postmaster@cio90012.visily.ai;
       dmarc=pass (p=QUARANTINE sp=QUARANTINE dis=NONE) header.from=visily.ai
DKIM-Signature: a=rsa-sha256; v=1; c=relaxed/relaxed; d=cio90012.visily.ai; q=dns/txt; s=mailo; t=1712732547; x=1712739747; h=Message-Id: List-Unsubscribe-Post: List-Unsubscribe: To: To: From: From: Subject: Subject: Content-Type: Mime-Version: Date: X-Feedback-Id: Sender; bh=UsYiM1Yfl4zaw8vLSwVotbL6uU83FtAGXKyd5jPctvw=; b=TsIvtLZJaNWVpoalD3OZ41Tu3Ru2D4oGLAkSOD8rRIZo1ccwnRAw1XpjlV5qXAt7HBGCIRd5oSi4/lg2jSxJQ+WjjOgsBAtsqStjZBNL/FMpX6XwdTQzoVNmcNaOsUt4aIg7O/aEY8KCQ9SOmhdFcAijpQpXnXjqRPHpbh4RHck=
DKIM-Signature: a=rsa-sha256; v=1; c=relaxed/relaxed; d=mailgun.org; q=dns/txt; s=mg; t=1712732547; x=1712739747; h=Message-Id: List-Unsubscribe-Post: List-Unsubscribe: To: To: From: From: Subject: Subject: Content-Type: Mime-Version: Date: X-Feedback-Id: Sender; bh=UsYiM1Yfl4zaw8vLSwVotbL6uU83FtAGXKyd5jPctvw=; b=AALhei2dsXog4N+hCwZtJ1FbLMgo0omya78mCFCzA/jwnvmmXGl1scChEmRbitsW8antw6VL/GQqpDRnMlVO9KLl5Uo0ctRH9t4oNSTX6yZIZpJlLmnmV4YZ8e92YZuRV8ZOVNpKBxJhySOlQh8LH9MwVgsZD0z7OThUQIcXjwk=
X-Feedback-Id: postmaster@cio90012.visily.ai::6486a42655ab5d20a39d19fb:mailgun
X-Mailgun-Sending-Ip: 159.112.241.114
X-Mailgun-Sid: WyI5ZTQyMiIsImFsZXhraXJvLmVkd0BnbWFpbC5jb20iLCJmNzY4N2M0Il0=
Received: from <unknown> (<unknown> []) by b2ee190d1bef with HTTP id 66160142a065d2cfac4e628e; Wed, 10 Apr 2024 03:02:26 GMT
Date: Wed, 10 Apr 2024 03:02:26 +0000
Mime-Version: 1.0
Content-Type: multipart/alternative; boundary="25111ff57bae4f18f7cc15d8b3af0c32faaae62f3b52709a52f9bef15ce6"
Subject: March releases: Slack integration and more!
From: Cassie from Visily <hello@visily.ai>
To: alexkiro.edw@gmail.com
X-Mailgun-Dkim: true
X-Mailgun-Native-Send: true
X-Mailgun-Track-Clicks: false
X-Mailgun-Track-Opens: false
X-Mailer: Customer.io (dgTtyQgDAPLgG_HgGwGOxfL85m7e5FIYG3FKrkE=; +https://whatis.customeriomail.com)
X-Report-Abuse-To: badactor@customer.io
List-Unsubscribe: <mailto:32.MRTVI5DZKFTUIQKQJRTUOX2IM5DXOR2PPBTEYOBVNU3WKNKGJFMUOM2GJNZGWRJ5@unsubscribe2.customer.io>, <https://e.customeriomail.com/unsubscribe/dgTtyQgDAPLgG_HgGwGOxfL85m7e5FIYG3FKrkE=>
List-Unsubscribe-Post: List-Unsubscribe=One-Click
X-Mailgun-Variables: {"email_id": "dgTtyQgDAPLgG_HgGwGOxfL85m7e5FIYG3FKrkE="}
Message-Id: <20240410030226.982787599410b759@cio90012.visily.ai>

--25111ff57bae4f18f7cc15d8b3af0c32faaae62f3b52709a52f9bef15ce6
Content-Transfer-Encoding: quoted-printable
Content-Type: text/plain; charset="utf-8"

( https://www.visily.ai/release-notes/release-note-v2-6-april-2024?utm_sour=
ce=3Dcustio&utm_medium=3Demail&utm_campaign=3Dmarch-wrap-up&utm_content=3Ds=
lack&utm_term=3Dcta-button#invite-teammates )
Visily now connects with Slack, so you can conveniently invite members from=
 Slack workspace to join your design boards in Visily!

Explore Visily x Slack=E2=80=99s new excitement! ( https://www.visily.ai/re=
lease-notes/release-note-v2-6-april-2024?utm_source=3Dcustio&utm_medium=3De=
mail&utm_campaign=3Dmarch-wrap-up&utm_content=3Dslack&utm_term=3Dcta-button=
#invite-teammates )
( https://www.visily.ai/release-notes/release-note-v2-6-april-2024?utm_sour=
ce=3Dcustio&utm_medium=3Demail&utm_campaign=3Dmarch-wrap-up&utm_content=3Ds=
lack&utm_term=3Dcta-button#invite-teammates )Visily now connects with Slack=
, so you can conveniently invite members from Slack workspace to join your =
design boards in Visily!

Explore Visily x Slack=E2=80=99s new excitement! ( https://www.visily.ai/re=
lease-notes/release-note-v2-6-april-2024?utm_source=3Dcustio&utm_medium=3De=
mail&utm_campaign=3Dmarch-wrap-up&utm_content=3Dslack&utm_term=3Dcta-button=
#invite-teammates )

( https://app.visily.ai/projects?type=3Dteam&utm_source=3Dcustio&utm_medium=
=3Demail&utm_campaign=3Dmarch-wrap-up&utm_content=3Dcreate-project&utm_term=
=3Dlink )Start a new project with AI

Kickstart your projects effortlessly using AI - from transforming screensho=
ts into designs to converting text into diagrams, Visily=E2=80=99s AI is yo=
ur best design buddy. =F0=9F=A7=8F=F0=9F=8F=BB=E2=80=8D=E2=99=80=EF=B8=8F

Start with AI =E2=86=92 ( https://app.visily.ai/projects?type=3Dteam&utm_so=
urce=3Dcustio&utm_medium=3Demail&utm_campaign=3Dmarch-wrap-up&utm_content=
=3Dcreate-project&utm_term=3Dlink )

( https://www.visily.ai/release-notes/release-note-v2-6-april-2024?utm_sour=
ce=3Dcustio&utm_medium=3Demail&utm_campaign=3Dmarch-wrap-up&utm_content=3Ds=
lack&utm_term=3Dlink#smart-components )Smart Components With More Flexibili=
ty

Our smart components just got a major upgrade. Our latest update gives you =
complete control over the appearance of smart components. You can now freel=
y adjust sizing, spacing and text styles.

Watch demo =E2=86=92 ( https://www.visily.ai/release-notes/release-note-v2-=
6-april-2024?utm_source=3Dcustio&utm_medium=3Demail&utm_campaign=3Dmarch-wr=
ap-up&utm_content=3Dslack&utm_term=3Dlink#smart-components )

( https://www.visily.ai/release-notes/release-note-v2-6-april-2024?utm_sour=
ce=3Dcustio&utm_medium=3Demail&utm_campaign=3Dmarch-wrap-up&utm_content=3Dd=
iagram-library&utm_term=3Dlink#diagram-library )Enjoy a Bigger & Better Dia=
gram Library

We've added many more brainstorming and diagram templates for various use c=
ases, such as user flows, sitemaps, project planning, product analysis, mee=
ting minutes, and more.

Explore our new templates =E2=86=92 ( https://www.visily.ai/release-notes/r=
elease-note-v2-6-april-2024?utm_source=3Dcustio&utm_medium=3Demail&utm_camp=
aign=3Dmarch-wrap-up&utm_content=3Ddiagram-library&utm_term=3Dlink#diagram-=
library )

( https://www.visily.ai/release-notes/release-note-v2-6-april-2024?utm_sour=
ce=3Dcustio&utm_medium=3Demail&utm_campaign=3Dmarch-wrap-up&utm_content=3Ds=
lack&utm_term=3Dlink#invite-teammates )
Collaborate Easier Than Ever

We=E2=80=99ve redesigned the =E2=80=9CInvite members to Workspace=E2=80=9D =
experience to be more intuitive and user-friendly.=C2=A0

Show me now =E2=86=92 ( https://www.visily.ai/release-notes/release-note-v2=
-6-april-2024?utm_source=3Dcustio&utm_medium=3Demail&utm_campaign=3Dmarch-w=
rap-up&utm_content=3Dslack&utm_term=3Dlink#invite-teammates )

( https://app.visily.ai/try/text_to_diagram?utm_source=3Dcustio&utm_medium=
=3Demail&utm_campaign=3Dmarch-wrap-up&utm_content=3Dtext-to-diagram&utm_ter=
m=3Dlink )Make Diagramming Effortless with Text to Diagram

Don=E2=80=99t miss out the AI feature: Text to Diagram =E2=9C=A8. Experienc=
e the simplicity of turning text into visuals with Text to Diagram.=C2=A0

Let AI streamline your design process =E2=86=92 ( https://app.visily.ai/try=
/text_to_diagram?utm_source=3Dcustio&utm_medium=3Demail&utm_campaign=3Dmarc=
h-wrap-up&utm_content=3Dtext-to-diagram&utm_term=3Dlink )

( https://www.youtube.com/playlist?list=3DPL12s5d3y1xCnJQ1w8d3QsDLM9JnYi0Z-=
b )Learn About AI Trends in Product Management

As AI capabilities advance, how will the role of product managers evolve? W=
hat new responsibilities will they take on? How can PMs take advantage of A=
I to build better products? Learn more from our audio blog series!

Check out the blog series =E2=86=92 ( https://www.youtube.com/playlist?list=
=3DPL12s5d3y1xCnJQ1w8d3QsDLM9JnYi0Z-b )

Head to the
design space ( https://app.visily.ai/?utm_source=3Dcustio&utm_medium=3Demai=
l&utm_campaign=3Dmarch-wrap-up&utm_content=3Dback-to-app&utm_term=3Dcta-but=
ton )

Head to the
design space ( https://app.visily.ai/?utm_source=3Dcustio&utm_medium=3Demai=
l&utm_campaign=3Dmarch-wrap-up&utm_content=3Dback-to-app&utm_term=3Dcta-but=
ton )
Visily, AI-powered app wireframing & prototyping

1776 Peachtree St. NW Suite 200N, Atlanta, GA, USA

Facebook ( https://www.facebook.com/visilyai )
Instagram ( https://www.instagram.com/visilyai/ )LinkedIn ( https://www.lin=
kedin.com/company/visilyai/ )Twitter ( https://twitter.com/i/flow/login?red=
irect_after_login=3D%2Fvisilyai )Visily ( https://www.visily.ai/ )

Unsubscribe ( http://track.customer.io/unsubscribe/dgTtyQgDAPLgG_HgGwGOxfL8=
5m7e5FIYG3FKrkE=3D )

Visily, AI-powered app wireframing & prototyping

1776 Peachtree St. NW Suite 200N, Atlanta, GA, USA

Facebook ( https://www.facebook.com/visilyai )Instagram ( https://www.insta=
gram.com/visilyai/ )LinkedIn ( https://www.linkedin.com/company/visilyai/ )=
Twitter ( https://twitter.com/i/flow/login?redirect_after_login=3D%2Fvisily=
ai )Visily ( https://www.visily.ai/ )

Unsubscribe ( http://track.customer.io/unsubscribe/dgTtyQgDAPLgG_HgGwGOxfL8=
5m7e5FIYG3FKrkE=3D )
--25111ff57bae4f18f7cc15d8b3af0c32faaae62f3b52709a52f9bef15ce6
Content-Transfer-Encoding: quoted-printable
Content-Type: text/html; charset="utf-8"

<!DOCTYPE html><html xmlns:v=3D"urn:schemas-microsoft-com:vml" xmlns:o=3D"u=
rn:schemas-microsoft-com:office:office" lang=3D"en"><head><title></title><m=
eta http-equiv=3D"Content-Type" content=3D"text/html; charset=3Dutf-8"/><me=
ta name=3D"viewport" content=3D"width=3Ddevice-width,initial-scale=3D1"/><!=
--[if mso]><xml><o:OfficeDocumentSettings><o:PixelsPerInch>96</o:PixelsPerI=
nch><o:AllowPNG/></o:OfficeDocumentSettings></xml><![endif]--><!--[if !mso]=
><!--><link href=3D"https://fonts.googleapis.com/css2?family=3DOpen+Sans:wg=
ht@400;700&amp;display=3Dswap" rel=3D"stylesheet" type=3D"text/css"/><!--<!=
[endif]--><style>
*{box-sizing:border-box}body{margin:0;padding:0}a[x-apple-data-detectors]{c=
olor:inherit!important;text-decoration:inherit!important}#MessageViewBody a=
{color:inherit;text-decoration:none}p{line-height:inherit}.desktop_hide,.de=
sktop_hide table{mso-hide:all;display:none;max-height:0;overflow:hidden}.im=
age_block img+div{display:none} @media (max-width:760px){.social_block.desk=
top_hide .social-table{display:inline-block!important}.image_block div.full=
Width{max-width:100%!important}.mobile_hide{display:none}.row-content{width=
:100%!important}.stack .column{width:100%;display:block}.mobile_hide{min-he=
ight:0;max-height:0;max-width:0;overflow:hidden;font-size:0}.desktop_hide,.=
desktop_hide table{display:table!important;max-height:none!important}.rever=
se{display:table;width:100%}.reverse .column.first{display:table-footer-gro=
up!important}.reverse .column.last{display:table-header-group!important}.ro=
w-10 td.column.first .border,.row-11 td.column.first .border,.row-13 td.col=
umn.first
.border,.row-15 td.column.first .border,.row-8 td.column.first .border,.row=
-9 td.column.first .border{padding:10px 20px 10px 60px;border-top:0;border-=
right:0;border-bottom:0;border-left:0}.row-10 td.column.last .border,.row-1=
1 td.column.last .border,.row-13 td.column.last .border,.row-15 td.column.l=
ast .border,.row-8 td.column.last .border,.row-9 td.column.last .border{pad=
ding:5px 40px 5px 20px;border-top:0;border-right:0;border-bottom:0;border-l=
eft:0}.row-2 .column-1 .block-1.image_block td.pad{padding:40px 0 20px!impo=
rtant}.row-2 .column-1 .block-2.image_block td.pad{padding:15px!important}.=
row-3 .column-1 .block-2.paragraph_block td.pad>div,.row-4 .column-1 .block=
-2.paragraph_block td.pad>div{text-align:center!important}.row-3 .column-1 =
.block-3.button_block a,.row-3 .column-1 .block-3.button_block div,.row-3 .=
column-1 .block-3.button_block span,.row-4 .column-1 .block-3.button_block =
a,.row-4 .column-1 .block-3.button_block div,.row-4 .column-1 .block-3.butt=
on_block
span{font-size:12px!important;line-height:24px!important}.row-1 .column-1,.=
row-5 .column-1,.row-6 .column-1 .block-1.image_block td.pad{padding:0!impo=
rtant}.row-10 .column-2 .block-1.paragraph_block td.pad>div,.row-11 .column=
-2 .block-1.paragraph_block td.pad>div,.row-13 .column-2 .block-1.paragraph=
_block td.pad>div,.row-15 .column-2 .block-1.paragraph_block td.pad>div,.ro=
w-8 .column-2 .block-1.paragraph_block td.pad>div,.row-9 .column-2 .block-1=
.paragraph_block td.pad>div{font-size:15px!important}.row-13 .column-2 .blo=
ck-1.paragraph_block td.pad,.row-15 .column-2 .block-1.paragraph_block td.p=
ad,.row-8 .column-2 .block-1.paragraph_block td.pad{padding:15px 24px 0!imp=
ortant}.row-10 .column-2 .block-2.paragraph_block td.pad>div,.row-10 .colum=
n-2 .block-3.paragraph_block td.pad>div,.row-11 .column-2 .block-2.paragrap=
h_block td.pad>div,.row-11 .column-2 .block-3.paragraph_block td.pad>div,.r=
ow-13 .column-2 .block-2.paragraph_block td.pad>div,.row-13 .column-2
.block-3.paragraph_block td.pad>div,.row-15 .column-2 .block-2.paragraph_bl=
ock td.pad>div,.row-15 .column-2 .block-3.paragraph_block td.pad>div,.row-8=
 .column-2 .block-2.paragraph_block td.pad>div,.row-8 .column-2 .block-3.pa=
ragraph_block td.pad>div,.row-9 .column-2 .block-2.paragraph_block td.pad>d=
iv,.row-9 .column-2 .block-3.paragraph_block td.pad>div{text-align:left!imp=
ortant}.row-10 .column-1 .border,.row-10 .column-2 .block-2.paragraph_block=
 td.pad,.row-10 .column-2 .block-3.paragraph_block td.pad,.row-11 .column-1=
 .border,.row-11 .column-2 .block-2.paragraph_block td.pad,.row-11 .column-=
2 .block-3.paragraph_block td.pad,.row-13 .column-1 .border,.row-13 .column=
-2 .block-2.paragraph_block td.pad,.row-13 .column-2 .block-3.paragraph_blo=
ck td.pad,.row-15 .column-1 .border,.row-15 .column-2 .block-2.paragraph_bl=
ock td.pad,.row-15 .column-2 .block-3.paragraph_block td.pad,.row-8 .column=
-1 .border,.row-8 .column-2 .block-2.paragraph_block td.pad,.row-8 .column-=
2
.block-3.paragraph_block td.pad,.row-9 .column-1 .border,.row-9 .column-2 .=
block-2.paragraph_block td.pad,.row-9 .column-2 .block-3.paragraph_block td=
.pad{padding:10px 24px!important}.row-10 .column-2 .block-1.paragraph_block=
 td.pad,.row-11 .column-2 .block-1.paragraph_block td.pad,.row-9 .column-2 =
.block-1.paragraph_block td.pad{padding:35px 24px 0!important}.row-3 .colum=
n-1,.row-4 .column-1{padding:1px 24px 30px!important}.row-7 .column-1{paddi=
ng:10px 0!important}.row-10 .column-2 .border,.row-11 .column-2 .border,.ro=
w-13 .column-2 .border,.row-15 .column-2 .border,.row-8 .column-2 .border,.=
row-9 .column-2 .border{padding:5px 20px 5px 0!important}.row-12 .column-1,=
.row-14 .column-1{padding:35px 24px 10px!important}.row-18 .column-1,.row-1=
9 .column-1{padding:15px 0 5px!important}}
</style></head><body style=3D"background-color:#f8f8fc;margin:0;padding:0;-=
webkit-text-size-adjust:none;text-size-adjust:none"><table class=3D"nl-cont=
ainer" width=3D"100%" border=3D"0" cellpadding=3D"0" cellspacing=3D"0" role=
=3D"presentation" style=3D"mso-table-lspace:0;mso-table-rspace:0;background=
-color:#f8f8fc;background-size:auto;background-image:none;background-positi=
on:top left;background-repeat:no-repeat"><tbody><tr><td><table class=3D"row=
 row-1" align=3D"center" width=3D"100%" border=3D"0" cellpadding=3D"0" cell=
spacing=3D"0" role=3D"presentation" style=3D"mso-table-lspace:0;mso-table-r=
space:0;background-color:#f1ecff"><tbody><tr><td><table class=3D"row-conten=
t stack" align=3D"center" border=3D"0" cellpadding=3D"0" cellspacing=3D"0" =
role=3D"presentation" style=3D"mso-table-lspace:0;mso-table-rspace:0;backgr=
ound-color:#f1ecff;border-radius:0;color:#000;width:740px;margin:0 auto" wi=
dth=3D"740"><tbody><tr><td class=3D"column column-1" width=3D"100%" style=
=3D"mso-table-lspace:0;mso-table-rspace:0;font-weight:400;text-align:left;p=
adding-bottom:10px;padding-top:20px;vertical-align:top;border-top:0;border-=
right:0;border-bottom:0;border-left:0"><table class=3D"empty_block block-1"=
 width=3D"100%" border=3D"0" cellpadding=3D"0" cellspacing=3D"0" role=3D"pr=
esentation" style=3D"mso-table-lspace:0;mso-table-rspace:0"><tbody><tr><td =
class=3D"pad"><div></div></td></tr></tbody></table></td></tr></tbody></tabl=
e></td></tr></tbody></table><table class=3D"row row-2" align=3D"center" wid=
th=3D"100%" border=3D"0" cellpadding=3D"0" cellspacing=3D"0" role=3D"presen=
tation" style=3D"mso-table-lspace:0;mso-table-rspace:0;background-color:#f1=
ecff;background-size:auto"><tbody><tr><td><table class=3D"row-content stack=
" align=3D"center" border=3D"0" cellpadding=3D"0" cellspacing=3D"0" role=3D=
"presentation" style=3D"mso-table-lspace:0;mso-table-rspace:0;background-si=
ze:auto;background-color:#fff;color:#000;border-radius:12px 12px 0 0;width:=
740px;margin:0 auto" width=3D"740"><tbody><tr><td class=3D"column column-1"=
 width=3D"100%" style=3D"mso-table-lspace:0;mso-table-rspace:0;font-weight:=
400;text-align:left;padding-bottom:5px;padding-top:5px;vertical-align:top;b=
order-top:0;border-right:0;border-bottom:0;border-left:0"><table class=3D"i=
mage_block block-1" width=3D"100%" border=3D"0" cellpadding=3D"0" cellspaci=
ng=3D"0" role=3D"presentation" style=3D"mso-table-lspace:0;mso-table-rspace=
:0"><tbody><tr><td class=3D"pad" style=3D"padding-bottom:20px;padding-top:2=
5px;width:100%;padding-right:0;padding-left:0"><div class=3D"alignment" ali=
gn=3D"center" style=3D"line-height:10px"><div style=3D"max-width:118.4px"><=
img src=3D"https://userimg-assets.customeriomail.com/images/client-env-1405=
25/1688371568845_Logo-min_01H4DCK8FSK86C9905R2X2KQP2.png" style=3D"display:=
block;height:auto;border:0;width:100%" width=3D"118.4" height=3D"auto"/></d=
iv></div></td></tr></tbody></table><table class=3D"image_block block-2" wid=
th=3D"100%" border=3D"0" cellpadding=3D"0" cellspacing=3D"0" role=3D"presen=
tation" style=3D"mso-table-lspace:0;mso-table-rspace:0"><tbody><tr><td clas=
s=3D"pad" style=3D"padding-bottom:5px;width:100%;padding-right:0;padding-le=
ft:0"><div class=3D"alignment" align=3D"center" style=3D"line-height:10px">=
<div class=3D"fullWidth" style=3D"max-width:370px"><img src=3D"https://user=
img-assets.customeriomail.com/images/client-env-140525/1712656889143_Group%=
201321314174-min_01HV14WDDDPYH2WXHJEPRX7TQA.png" style=3D"display:block;hei=
ght:auto;border:0;width:100%" width=3D"370" height=3D"auto"/></div></div></=
td></tr></tbody></table></td></tr></tbody></table></td></tr></tbody></table=
><table class=3D"row row-3 mobile_hide" align=3D"center" width=3D"100%" bor=
der=3D"0" cellpadding=3D"0" cellspacing=3D"0" role=3D"presentation" style=
=3D"mso-table-lspace:0;mso-table-rspace:0;background-color:#f1ecff;backgrou=
nd-size:auto"><tbody><tr><td><table class=3D"row-content stack" align=3D"ce=
nter" border=3D"0" cellpadding=3D"0" cellspacing=3D"0" role=3D"presentation=
" style=3D"mso-table-lspace:0;mso-table-rspace:0;background-color:#fff;colo=
r:#000;background-size:auto;border-radius:6px;width:740px;margin:0 auto" wi=
dth=3D"740">
<tbody><tr><td class=3D"column column-1" width=3D"100%" style=3D"mso-table-=
lspace:0;mso-table-rspace:0;font-weight:400;text-align:left;padding-bottom:=
16px;padding-left:60px;padding-right:60px;padding-top:34px;vertical-align:t=
op;border-top:0;border-right:0;border-bottom:0;border-left:0"><table class=
=3D"image_block block-1" width=3D"100%" border=3D"0" cellpadding=3D"0" cell=
spacing=3D"0" role=3D"presentation" style=3D"mso-table-lspace:0;mso-table-r=
space:0"><tbody><tr><td class=3D"pad" style=3D"width:100%"><div class=3D"al=
ignment" align=3D"center" style=3D"line-height:10px"><div style=3D"max-widt=
h:620px"><a href=3D"https://e.customeriomail.com/e/c/eyJlbWFpbF9pZCI6ImRnVH=
R5UWdEQVBMZ0dfSGdHd0dPeGZMODVtN2U1RklZRzNGS3JrRT0iLCJocmVmIjoiaHR0cHM6Ly93d=
3cudmlzaWx5LmFpL3JlbGVhc2Utbm90ZXMvcmVsZWFzZS1ub3RlLXYyLTYtYXByaWwtMjAyND91=
dG1fc291cmNlPWN1c3Rpb1x1MDAyNnV0bV9tZWRpdW09ZW1haWxcdTAwMjZ1dG1fY2FtcGFpZ24=
9bWFyY2gtd3JhcC11cFx1MDAyNnV0bV9jb250ZW50PXNsYWNrXHUwMDI2dXRtX3Rlcm09Y3RhLW=
J1dHRvbiNpbnZpdGUtdGVhbW1hdGVzIiwiaW50ZXJuYWwiOiJlZGM5MDgwZmExMjVmMmUwMWIiL=
CJsaW5rX2lkIjoxMTI0fQ/1c09278f56b85c034b653c2c7a09ff14b7e832deeb8e98d1c4bd9=
0722b16fc41" target=3D"_blank" style=3D"outline:none" tabindex=3D"-1"><img =
src=3D"https://userimg-assets.customeriomail.com/images/client-env-140525/1=
712639032551_Hero%20banner-min_01HV0KVFAKKRDSSQJD5ESH9AQN.png" style=3D"dis=
play:block;height:auto;border:0;width:100%" width=3D"620" height=3D"auto"/>=
</a></div></div></td></tr></tbody></table><table class=3D"paragraph_block b=
lock-2" width=3D"100%" border=3D"0" cellpadding=3D"0" cellspacing=3D"0" rol=
e=3D"presentation" style=3D"mso-table-lspace:0;mso-table-rspace:0;word-brea=
k:break-word"><tbody><tr><td class=3D"pad" style=3D"padding-bottom:24px;pad=
ding-top:24px"><div style=3D"color:#12101a;direction:ltr;font-family:&#39;O=
pen Sans&#39;,&#39;Helvetica Neue&#39;,Helvetica,Arial,sans-serif;font-size=
:14px;font-weight:400;letter-spacing:0;line-height:150%;text-align:left;mso=
-line-height-alt:21px"><p style=3D"margin:0">
Visily now connects with Slack, so you can conveniently invite members from=
 Slack workspace to join your design boards in Visily!</p></div></td></tr><=
/tbody></table><table class=3D"button_block block-3" width=3D"100%" border=
=3D"0" cellpadding=3D"0" cellspacing=3D"0" role=3D"presentation" style=3D"m=
so-table-lspace:0;mso-table-rspace:0"><tbody><tr><td class=3D"pad" style=3D=
"text-align:center"><div class=3D"alignment" align=3D"center"><!--[if mso]>
<v:roundrect xmlns:v=3D"urn:schemas-microsoft-com:vml" xmlns:w=3D"urn:schem=
as-microsoft-com:office:word" href=3D"https://e.customeriomail.com/e/c/eyJl=
bWFpbF9pZCI6ImRnVHR5UWdEQVBMZ0dfSGdHd0dPeGZMODVtN2U1RklZRzNGS3JrRT0iLCJocmV=
mIjoiaHR0cHM6Ly93d3cudmlzaWx5LmFpL3JlbGVhc2Utbm90ZXMvcmVsZWFzZS1ub3RlLXYyLT=
YtYXByaWwtMjAyND91dG1fc291cmNlPWN1c3Rpb1x1MDAyNnV0bV9tZWRpdW09ZW1haWxcdTAwM=
jZ1dG1fY2FtcGFpZ249bWFyY2gtd3JhcC11cFx1MDAyNnV0bV9jb250ZW50PXNsYWNrXHUwMDI2=
dXRtX3Rlcm09Y3RhLWJ1dHRvbiNpbnZpdGUtdGVhbW1hdGVzIiwiaW50ZXJuYWwiOiJlZGM5MDg=
wZmExMjVmMmUwMWIiLCJsaW5rX2lkIjoxMTI0fQ/1c09278f56b85c034b653c2c7a09ff14b7e=
832deeb8e98d1c4bd90722b16fc41" style=3D"height:44px;width:302px;v-text-anch=
or:middle;" arcsize=3D"19%" stroke=3D"false" fillcolor=3D"#6454d6">
<w:anchorlock/>
<v:textbox inset=3D"0px,0px,0px,0px">
<center style=3D"color:#ffffff; font-family:Arial, sans-serif; font-size:14=
px">
<![endif]-->
<a href=3D"https://e.customeriomail.com/e/c/eyJlbWFpbF9pZCI6ImRnVHR5UWdEQVB=
MZ0dfSGdHd0dPeGZMODVtN2U1RklZRzNGS3JrRT0iLCJocmVmIjoiaHR0cHM6Ly93d3cudmlzaW=
x5LmFpL3JlbGVhc2Utbm90ZXMvcmVsZWFzZS1ub3RlLXYyLTYtYXByaWwtMjAyND91dG1fc291c=
mNlPWN1c3Rpb1x1MDAyNnV0bV9tZWRpdW09ZW1haWxcdTAwMjZ1dG1fY2FtcGFpZ249bWFyY2gt=
d3JhcC11cFx1MDAyNnV0bV9jb250ZW50PXNsYWNrXHUwMDI2dXRtX3Rlcm09Y3RhLWJ1dHRvbiN=
pbnZpdGUtdGVhbW1hdGVzIiwiaW50ZXJuYWwiOiJlZGM5MDgwZmExMjVmMmUwMWIiLCJsaW5rX2=
lkIjoxMTI0fQ/1c09278f56b85c034b653c2c7a09ff14b7e832deeb8e98d1c4bd90722b16fc=
41" target=3D"_blank" style=3D"text-decoration:none;display:inline-block;co=
lor:#ffffff;background-color:#6454d6;border-radius:8px;width:auto;border-to=
p:0px solid transparent;font-weight:400;border-right:0px solid transparent;=
border-bottom:0px solid transparent;border-left:0px solid transparent;paddi=
ng-top:8px;padding-bottom:8px;font-family:&#39;Open Sans&#39;, &#39;Helveti=
ca Neue&#39;, Helvetica, Arial, sans-serif;font-size:14px;text-align:center=
;mso-border-alt:none;word-break:keep-all;"><span style=3D"padding-left:14px=
;padding-right:14px;font-size:14px;display:inline-block;letter-spacing:norm=
al;"><span style=3D"word-break: break-word; line-height: 28px;"><strong>Exp=
lore Visily x Slack=E2=80=99s new excitement!</strong></span></span></a>
<!--[if mso]></center></v:textbox></v:roundrect><![endif]--></div></td></tr=
></tbody></table></td></tr></tbody></table></td></tr></tbody></table><table=
 class=3D"row row-4 desktop_hide" align=3D"center" width=3D"100%" border=3D=
"0" cellpadding=3D"0" cellspacing=3D"0" role=3D"presentation" style=3D"mso-=
table-lspace:0;mso-table-rspace:0;mso-hide:all;display:none;max-height:0;ov=
erflow:hidden;background-color:#f1ecff;background-size:auto"><tbody><tr><td=
><table class=3D"row-content stack" align=3D"center" border=3D"0" cellpaddi=
ng=3D"0" cellspacing=3D"0" role=3D"presentation" style=3D"mso-table-lspace:=
0;mso-table-rspace:0;mso-hide:all;display:none;max-height:0;overflow:hidden=
;background-color:#fff;color:#000;background-size:auto;border-radius:6px;wi=
dth:740px;margin:0 auto" width=3D"740"><tbody><tr><td class=3D"column colum=
n-1" width=3D"100%" style=3D"mso-table-lspace:0;mso-table-rspace:0;font-wei=
ght:400;text-align:left;padding-bottom:16px;padding-left:24px;padding-right=
:24px;padding-top:14px;vertical-align:top;border-top:0;border-right:0;borde=
r-bottom:0;border-left:0"><table class=3D"image_block block-1" width=3D"100=
%" border=3D"0" cellpadding=3D"0" cellspacing=3D"0" role=3D"presentation" s=
tyle=3D"mso-table-lspace:0;mso-table-rspace:0;mso-hide:all;display:none;max=
-height:0;overflow:hidden"><tbody><tr><td class=3D"pad" style=3D"width:100%=
"><div class=3D"alignment" align=3D"center" style=3D"line-height:10px"><div=
 style=3D"max-width:692px"><a href=3D"https://e.customeriomail.com/e/c/eyJl=
bWFpbF9pZCI6ImRnVHR5UWdEQVBMZ0dfSGdHd0dPeGZMODVtN2U1RklZRzNGS3JrRT0iLCJocmV=
mIjoiaHR0cHM6Ly93d3cudmlzaWx5LmFpL3JlbGVhc2Utbm90ZXMvcmVsZWFzZS1ub3RlLXYyLT=
YtYXByaWwtMjAyND91dG1fc291cmNlPWN1c3Rpb1x1MDAyNnV0bV9tZWRpdW09ZW1haWxcdTAwM=
jZ1dG1fY2FtcGFpZ249bWFyY2gtd3JhcC11cFx1MDAyNnV0bV9jb250ZW50PXNsYWNrXHUwMDI2=
dXRtX3Rlcm09Y3RhLWJ1dHRvbiNpbnZpdGUtdGVhbW1hdGVzIiwiaW50ZXJuYWwiOiJlZGM5MDg=
wZmExMjVmMmUwMWIiLCJsaW5rX2lkIjoxMTI0fQ/1c09278f56b85c034b653c2c7a09ff14b7e=
832deeb8e98d1c4bd90722b16fc41" target=3D"_blank" style=3D"outline:none" tab=
index=3D"-1"><img src=3D"https://userimg-assets.customeriomail.com/images/c=
lient-env-140525/1712639032551_Hero%20banner-min_01HV0KVFAKKRDSSQJD5ESH9AQN=
.png" style=3D"display:block;height:auto;border:0;width:100%" width=3D"692"=
 height=3D"auto"/></a></div></div></td></tr></tbody></table><table class=3D=
"paragraph_block block-2" width=3D"100%" border=3D"0" cellpadding=3D"0" cel=
lspacing=3D"0" role=3D"presentation" style=3D"mso-table-lspace:0;mso-table-=
rspace:0;word-break:break-word;mso-hide:all;display:none;max-height:0;overf=
low:hidden"><tbody><tr><td class=3D"pad" style=3D"padding-bottom:24px;paddi=
ng-top:24px"><div style=3D"color:#12101a;direction:ltr;font-family:&#39;Ope=
n Sans&#39;,&#39;Helvetica Neue&#39;,Helvetica,Arial,sans-serif;font-size:1=
4px;font-weight:400;letter-spacing:0;line-height:150%;text-align:center;mso=
-line-height-alt:21px"><p style=3D"margin:0">Visily now connects with Slack=
, so you can conveniently invite members from Slack workspace to join your =
design boards in Visily!</p></div></td></tr></tbody></table><table class=3D=
"button_block block-3" width=3D"100%" border=3D"0" cellpadding=3D"0" cellsp=
acing=3D"0" role=3D"presentation" style=3D"mso-table-lspace:0;mso-table-rsp=
ace:0;mso-hide:all;display:none;max-height:0;overflow:hidden"><tbody><tr><t=
d class=3D"pad" style=3D"text-align:center"><div class=3D"alignment" align=
=3D"center"><!--[if mso]>
<v:roundrect xmlns:v=3D"urn:schemas-microsoft-com:vml" xmlns:w=3D"urn:schem=
as-microsoft-com:office:word" href=3D"https://e.customeriomail.com/e/c/eyJl=
bWFpbF9pZCI6ImRnVHR5UWdEQVBMZ0dfSGdHd0dPeGZMODVtN2U1RklZRzNGS3JrRT0iLCJocmV=
mIjoiaHR0cHM6Ly93d3cudmlzaWx5LmFpL3JlbGVhc2Utbm90ZXMvcmVsZWFzZS1ub3RlLXYyLT=
YtYXByaWwtMjAyND91dG1fc291cmNlPWN1c3Rpb1x1MDAyNnV0bV9tZWRpdW09ZW1haWxcdTAwM=
jZ1dG1fY2FtcGFpZ249bWFyY2gtd3JhcC11cFx1MDAyNnV0bV9jb250ZW50PXNsYWNrXHUwMDI2=
dXRtX3Rlcm09Y3RhLWJ1dHRvbiNpbnZpdGUtdGVhbW1hdGVzIiwiaW50ZXJuYWwiOiJlZGM5MDg=
wZmExMjVmMmUwMWIiLCJsaW5rX2lkIjoxMTI0fQ/1c09278f56b85c034b653c2c7a09ff14b7e=
832deeb8e98d1c4bd90722b16fc41" style=3D"height:44px;width:302px;v-text-anch=
or:middle;" arcsize=3D"19%" stroke=3D"false" fillcolor=3D"#6454d6">
<w:anchorlock/>
<v:textbox inset=3D"0px,0px,0px,0px">
<center style=3D"color:#ffffff; font-family:Arial, sans-serif; font-size:14=
px">
<![endif]-->
<a href=3D"https://e.customeriomail.com/e/c/eyJlbWFpbF9pZCI6ImRnVHR5UWdEQVB=
MZ0dfSGdHd0dPeGZMODVtN2U1RklZRzNGS3JrRT0iLCJocmVmIjoiaHR0cHM6Ly93d3cudmlzaW=
x5LmFpL3JlbGVhc2Utbm90ZXMvcmVsZWFzZS1ub3RlLXYyLTYtYXByaWwtMjAyND91dG1fc291c=
mNlPWN1c3Rpb1x1MDAyNnV0bV9tZWRpdW09ZW1haWxcdTAwMjZ1dG1fY2FtcGFpZ249bWFyY2gt=
d3JhcC11cFx1MDAyNnV0bV9jb250ZW50PXNsYWNrXHUwMDI2dXRtX3Rlcm09Y3RhLWJ1dHRvbiN=
pbnZpdGUtdGVhbW1hdGVzIiwiaW50ZXJuYWwiOiJlZGM5MDgwZmExMjVmMmUwMWIiLCJsaW5rX2=
lkIjoxMTI0fQ/1c09278f56b85c034b653c2c7a09ff14b7e832deeb8e98d1c4bd90722b16fc=
41" target=3D"_blank" style=3D"text-decoration:none;display:inline-block;co=
lor:#ffffff;background-color:#6454d6;border-radius:8px;width:auto;border-to=
p:0px solid transparent;font-weight:400;border-right:0px solid transparent;=
border-bottom:0px solid transparent;border-left:0px solid transparent;paddi=
ng-top:8px;padding-bottom:8px;font-family:&#39;Open Sans&#39;, &#39;Helveti=
ca Neue&#39;, Helvetica, Arial, sans-serif;font-size:14px;text-align:center=
;mso-border-alt:none;word-break:keep-all;"><span style=3D"padding-left:14px=
;padding-right:14px;font-size:14px;display:inline-block;letter-spacing:norm=
al;"><span style=3D"word-break: break-word; line-height: 28px;"><strong>Exp=
lore Visily x Slack=E2=80=99s new excitement!</strong></span></span></a>
<!--[if mso]></center></v:textbox></v:roundrect><![endif]--></div></td></tr=
></tbody></table></td></tr></tbody></table></td></tr></tbody></table><table=
 class=3D"row row-5" align=3D"center" width=3D"100%" border=3D"0" cellpaddi=
ng=3D"0" cellspacing=3D"0" role=3D"presentation" style=3D"mso-table-lspace:=
0;mso-table-rspace:0;background-color:#f1ecff"><tbody><tr><td><table class=
=3D"row-content stack" align=3D"center" border=3D"0" cellpadding=3D"0" cell=
spacing=3D"0" role=3D"presentation" style=3D"mso-table-lspace:0;mso-table-r=
space:0;background-color:#fff;border-radius:0;color:#000;width:740px;margin=
:0 auto" width=3D"740"><tbody><tr><td class=3D"column column-1" width=3D"10=
0%" style=3D"mso-table-lspace:0;mso-table-rspace:0;font-weight:400;text-ali=
gn:left;padding-bottom:20px;padding-top:10px;vertical-align:top;border-top:=
0;border-right:0;border-bottom:0;border-left:0"><table class=3D"empty_block=
 block-1" width=3D"100%" border=3D"0" cellpadding=3D"0" cellspacing=3D"0" r=
ole=3D"presentation" style=3D"mso-table-lspace:0;mso-table-rspace:0"><tbody=
><tr><td class=3D"pad"><div></div></td></tr></tbody></table></td></tr></tbo=
dy></table></td></tr></tbody></table><table class=3D"row row-6" align=3D"ce=
nter" width=3D"100%" border=3D"0" cellpadding=3D"0" cellspacing=3D"0" role=
=3D"presentation" style=3D"mso-table-lspace:0;mso-table-rspace:0;background=
-color:#f1ecff"><tbody><tr><td><table class=3D"row-content stack" align=3D"=
center" border=3D"0" cellpadding=3D"0" cellspacing=3D"0" role=3D"presentati=
on" style=3D"mso-table-lspace:0;mso-table-rspace:0;background-color:#fff;bo=
rder-radius:0;color:#000;width:740px;margin:0 auto" width=3D"740"><tbody><t=
r><td class=3D"column column-1" width=3D"100%" style=3D"mso-table-lspace:0;=
mso-table-rspace:0;font-weight:400;text-align:left;padding-left:40px;paddin=
g-right:40px;vertical-align:top;border-top:0;border-right:0;border-bottom:0=
;border-left:0"><table class=3D"image_block block-1" width=3D"100%" border=
=3D"0" cellpadding=3D"0" cellspacing=3D"0" role=3D"presentation" style=3D"m=
so-table-lspace:0;mso-table-rspace:0"><tbody><tr><td class=3D"pad" style=3D=
"width:100%;padding-right:0;padding-left:0"><div class=3D"alignment" align=
=3D"center" style=3D"line-height:10px"><div class=3D"fullWidth" style=3D"ma=
x-width:363px"><img src=3D"https://userimg-assets.customeriomail.com/images=
/client-env-140525/1712639031091_February%E2%80%99s%20Highlights-min_01HV0K=
VDWQTNABFGSXXTFPMS3M.png" style=3D"display:block;height:auto;border:0;width=
:100%" width=3D"363" height=3D"auto"/></div></div></td></tr></tbody></table=
></td>
</tr></tbody></table></td></tr></tbody></table><table class=3D"row row-7" a=
lign=3D"center" width=3D"100%" border=3D"0" cellpadding=3D"0" cellspacing=
=3D"0" role=3D"presentation" style=3D"mso-table-lspace:0;mso-table-rspace:0=
;background-color:#f1ecff"><tbody><tr><td><table class=3D"row-content stack=
" align=3D"center" border=3D"0" cellpadding=3D"0" cellspacing=3D"0" role=3D=
"presentation" style=3D"mso-table-lspace:0;mso-table-rspace:0;background-co=
lor:#fff;border-radius:0;color:#000;width:740px;margin:0 auto" width=3D"740=
"><tbody>
<tr><td class=3D"column column-1" width=3D"100%" style=3D"mso-table-lspace:=
0;mso-table-rspace:0;font-weight:400;text-align:left;padding-bottom:10px;pa=
dding-top:20px;vertical-align:top;border-top:0;border-right:0;border-bottom=
:0;border-left:0"><table class=3D"empty_block block-1" width=3D"100%" borde=
r=3D"0" cellpadding=3D"0" cellspacing=3D"0" role=3D"presentation" style=3D"=
mso-table-lspace:0;mso-table-rspace:0"><tbody><tr><td class=3D"pad"><div></=
div></td></tr></tbody></table></td></tr></tbody></table></td></tr></tbody><=
/table>
<table class=3D"row row-8" align=3D"center" width=3D"100%" border=3D"0" cel=
lpadding=3D"0" cellspacing=3D"0" role=3D"presentation" style=3D"mso-table-l=
space:0;mso-table-rspace:0;background-color:#f1ecff"><tbody><tr><td><table =
class=3D"row-content stack" align=3D"center" border=3D"0" cellpadding=3D"0"=
 cellspacing=3D"0" role=3D"presentation" style=3D"mso-table-lspace:0;mso-ta=
ble-rspace:0;background-color:#fff;border-radius:0;color:#000;width:740px;m=
argin:0 auto" width=3D"740"><tbody><tr class=3D"reverse"><td class=3D"colum=
n column-1 first" width=3D"33.333333333333336%" style=3D"mso-table-lspace:0=
;mso-table-rspace:0;font-weight:400;text-align:left;padding-bottom:10px;pad=
ding-left:60px;padding-right:20px;padding-top:10px;vertical-align:middle;bo=
rder-top:0;border-right:0;border-bottom:0;border-left:0"><div class=3D"bord=
er"><table class=3D"image_block block-1" width=3D"100%" border=3D"0" cellpa=
dding=3D"0" cellspacing=3D"0" role=3D"presentation" style=3D"mso-table-lspa=
ce:0;mso-table-rspace:0"><tbody><tr><td class=3D"pad" style=3D"width:100%;p=
adding-right:0;padding-left:0"><div class=3D"alignment" align=3D"left" styl=
e=3D"line-height:10px"><div class=3D"fullWidth" style=3D"max-width:166.667p=
x"><a href=3D"https://e.customeriomail.com/e/c/eyJlbWFpbF9pZCI6ImRnVHR5UWdE=
QVBMZ0dfSGdHd0dPeGZMODVtN2U1RklZRzNGS3JrRT0iLCJocmVmIjoiaHR0cHM6Ly9hcHAudml=
zaWx5LmFpL3Byb2plY3RzP3R5cGU9dGVhbVx1MDAyNnV0bV9zb3VyY2U9Y3VzdGlvXHUwMDI2dX=
RtX21lZGl1bT1lbWFpbFx1MDAyNnV0bV9jYW1wYWlnbj1tYXJjaC13cmFwLXVwXHUwMDI2dXRtX=
2NvbnRlbnQ9Y3JlYXRlLXByb2plY3RcdTAwMjZ1dG1fdGVybT1saW5rIiwiaW50ZXJuYWwiOiJl=
ZGM5MDgwZmExMjVmMmUwMWIiLCJsaW5rX2lkIjoxMTI1fQ/0074030dc8e9c49303e4e812771a=
1169d9700d8a4b1a7e2d724181fed0b33741" target=3D"_blank" style=3D"outline:no=
ne" tabindex=3D"-1"><img src=3D"https://userimg-assets.customeriomail.com/i=
mages/client-env-140525/1712639923209_Mar-wrap-up-6_01HV0MPN4BCTGWXG3T9BTFV=
WMM.png" style=3D"display:block;height:auto;border:0;width:100%" width=3D"1=
66.667" height=3D"auto"/>
</a></div></div></td></tr></tbody></table></div></td><td class=3D"column co=
lumn-2 last" width=3D"66.66666666666667%" style=3D"mso-table-lspace:0;mso-t=
able-rspace:0;font-weight:400;text-align:left;padding-bottom:5px;padding-le=
ft:20px;padding-right:40px;padding-top:5px;vertical-align:middle;border-top=
:0;border-right:0;border-bottom:0;border-left:0"><div class=3D"border"><tab=
le class=3D"paragraph_block block-1" width=3D"100%" border=3D"0" cellpaddin=
g=3D"0" cellspacing=3D"0" role=3D"presentation" style=3D"mso-table-lspace:0=
;mso-table-rspace:0;word-break:break-word"><tbody><tr><td class=3D"pad" sty=
le=3D"padding-bottom:10px"><div style=3D"color:#6454d6;direction:ltr;font-f=
amily:&#39;Open Sans&#39;,&#39;Helvetica Neue&#39;,Helvetica,Arial,sans-ser=
if;font-size:14px;font-weight:700;letter-spacing:0;line-height:150%;text-al=
ign:left;mso-line-height-alt:21px"><p style=3D"margin:0">Start a new projec=
t with AI</p></div></td></tr></tbody></table><table class=3D"paragraph_bloc=
k block-2" width=3D"100%" border=3D"0" cellpadding=3D"0" cellspacing=3D"0" =
role=3D"presentation" style=3D"mso-table-lspace:0;mso-table-rspace:0;word-b=
reak:break-word"><tbody><tr><td class=3D"pad" style=3D"padding-right:15px">=
<div style=3D"color:#1a1a1a;direction:ltr;font-family:&#39;Open Sans&#39;,&=
#39;Helvetica Neue&#39;,Helvetica,Arial,sans-serif;font-size:14px;font-weig=
ht:400;letter-spacing:0;line-height:150%;text-align:left;mso-line-height-al=
t:21px"><p style=3D"margin:0">
Kickstart your projects effortlessly using AI - from transforming screensho=
ts into designs to converting text into diagrams, Visily=E2=80=99s AI is yo=
ur best design buddy. =F0=9F=A7=8F=F0=9F=8F=BB=E2=80=8D=E2=99=80=EF=B8=8F</=
p></div></td></tr></tbody></table><table class=3D"paragraph_block block-3" =
width=3D"100%" border=3D"0" cellpadding=3D"0" cellspacing=3D"0" role=3D"pre=
sentation" style=3D"mso-table-lspace:0;mso-table-rspace:0;word-break:break-=
word"><tbody><tr><td class=3D"pad" style=3D"padding-right:15px;padding-top:=
10px"><div style=3D"color:#6454d6;direction:ltr;font-family:&#39;Open Sans&=
#39;,&#39;Helvetica Neue&#39;,Helvetica,Arial,sans-serif;font-size:14px;fon=
t-weight:400;letter-spacing:0;line-height:150%;text-align:left;mso-line-hei=
ght-alt:21px"><p style=3D"margin:0"><a href=3D"https://e.customeriomail.com=
/e/c/eyJlbWFpbF9pZCI6ImRnVHR5UWdEQVBMZ0dfSGdHd0dPeGZMODVtN2U1RklZRzNGS3JrRT=
0iLCJocmVmIjoiaHR0cHM6Ly9hcHAudmlzaWx5LmFpL3Byb2plY3RzP3R5cGU9dGVhbVx1MDAyN=
nV0bV9zb3VyY2U9Y3VzdGlvXHUwMDI2dXRtX21lZGl1bT1lbWFpbFx1MDAyNnV0bV9jYW1wYWln=
bj1tYXJjaC13cmFwLXVwXHUwMDI2dXRtX2NvbnRlbnQ9Y3JlYXRlLXByb2plY3RcdTAwMjZ1dG1=
fdGVybT1saW5rIiwiaW50ZXJuYWwiOiJlZGM5MDgwZmExMjVmMmUwMWIiLCJsaW5rX2lkIjoxMT=
I1fQ/0074030dc8e9c49303e4e812771a1169d9700d8a4b1a7e2d724181fed0b33741" targ=
et=3D"_blank" style=3D"text-decoration: none; color: #6454d6;" rel=3D"noope=
ner">Start with AI <strong>=E2=86=92</strong></a></p></div></td></tr></tbod=
y></table></div></td></tr></tbody></table></td></tr></tbody></table><table =
class=3D"row row-9" align=3D"center" width=3D"100%" border=3D"0" cellpaddin=
g=3D"0" cellspacing=3D"0" role=3D"presentation" style=3D"mso-table-lspace:0=
;mso-table-rspace:0;background-color:#f1ecff"><tbody><tr><td><table class=
=3D"row-content stack" align=3D"center" border=3D"0" cellpadding=3D"0" cell=
spacing=3D"0" role=3D"presentation" style=3D"mso-table-lspace:0;mso-table-r=
space:0;background-color:#fff;border-radius:0;color:#000;width:740px;margin=
:0 auto" width=3D"740"><tbody><tr class=3D"reverse"><td class=3D"column col=
umn-1 first" width=3D"33.333333333333336%" style=3D"mso-table-lspace:0;mso-=
table-rspace:0;font-weight:400;text-align:left;padding-bottom:10px;padding-=
left:60px;padding-right:20px;padding-top:10px;vertical-align:middle;border-=
top:0;border-right:0;border-bottom:0;border-left:0"><div class=3D"border"><=
table class=3D"image_block block-1" width=3D"100%" border=3D"0" cellpadding=
=3D"0" cellspacing=3D"0" role=3D"presentation" style=3D"mso-table-lspace:0;=
mso-table-rspace:0"><tbody><tr><td class=3D"pad" style=3D"width:100%"><div =
class=3D"alignment" align=3D"left" style=3D"line-height:10px"><div class=3D=
"fullWidth" style=3D"max-width:166.667px"><a href=3D"https://e.customerioma=
il.com/e/c/eyJlbWFpbF9pZCI6ImRnVHR5UWdEQVBMZ0dfSGdHd0dPeGZMODVtN2U1RklZRzNG=
S3JrRT0iLCJocmVmIjoiaHR0cHM6Ly93d3cudmlzaWx5LmFpL3JlbGVhc2Utbm90ZXMvcmVsZWF=
zZS1ub3RlLXYyLTYtYXByaWwtMjAyND91dG1fc291cmNlPWN1c3Rpb1x1MDAyNnV0bV9tZWRpdW=
09ZW1haWxcdTAwMjZ1dG1fY2FtcGFpZ249bWFyY2gtd3JhcC11cFx1MDAyNnV0bV9jb250ZW50P=
XNsYWNrXHUwMDI2dXRtX3Rlcm09bGluayNzbWFydC1jb21wb25lbnRzIiwiaW50ZXJuYWwiOiJl=
ZGM5MDgwZmExMjVmMmUwMWIiLCJsaW5rX2lkIjoxMTI2fQ/d66493c3eef54da7b79b6963a633=
5418a20208c44c9d1cd15398642c0319e807" target=3D"_blank" style=3D"outline:no=
ne" tabindex=3D"-1"><img src=3D"https://userimg-assets.customeriomail.com/i=
mages/client-env-140525/1712639922193_Mar-wrap-up-5_01HV0MPM4MNGH9K2BSZMSJ3=
9EJ.png" style=3D"display:block;height:auto;border:0;width:100%" width=3D"1=
66.667" height=3D"auto"/></a></div></div></td></tr></tbody></table></div></=
td><td class=3D"column column-2 last" width=3D"66.66666666666667%" style=3D=
"mso-table-lspace:0;mso-table-rspace:0;font-weight:400;text-align:left;padd=
ing-bottom:5px;padding-left:20px;padding-right:40px;padding-top:5px;vertica=
l-align:middle;border-top:0;border-right:0;border-bottom:0;border-left:0"><=
div class=3D"border"><table class=3D"paragraph_block block-1" width=3D"100%=
" border=3D"0" cellpadding=3D"0" cellspacing=3D"0" role=3D"presentation" st=
yle=3D"mso-table-lspace:0;mso-table-rspace:0;word-break:break-word"><tbody>=
<tr><td class=3D"pad" style=3D"padding-bottom:10px"><div style=3D"color:#64=
54d6;direction:ltr;font-family:&#39;Open Sans&#39;,&#39;Helvetica Neue&#39;=
,Helvetica,Arial,sans-serif;font-size:14px;font-weight:700;letter-spacing:0=
;line-height:150%;text-align:left;mso-line-height-alt:21px"><p style=3D"mar=
gin:0">Smart Components With More Flexibility</p></div></td></tr></tbody></=
table><table class=3D"paragraph_block block-2" width=3D"100%" border=3D"0" =
cellpadding=3D"0" cellspacing=3D"0" role=3D"presentation" style=3D"mso-tabl=
e-lspace:0;mso-table-rspace:0;word-break:break-word"><tbody><tr><td class=
=3D"pad" style=3D"padding-right:15px"><div style=3D"color:#1a1a1a;direction=
:ltr;font-family:&#39;Open Sans&#39;,&#39;Helvetica Neue&#39;,Helvetica,Ari=
al,sans-serif;font-size:14px;font-weight:400;letter-spacing:0;line-height:1=
50%;text-align:left;mso-line-height-alt:21px"><p style=3D"margin:0">
Our smart components just got a major upgrade. Our latest update gives you =
complete control over the appearance of smart components. You can now freel=
y adjust sizing, spacing and text styles.</p></div></td></tr></tbody></tabl=
e><table class=3D"paragraph_block block-3" width=3D"100%" border=3D"0" cell=
padding=3D"0" cellspacing=3D"0" role=3D"presentation" style=3D"mso-table-ls=
pace:0;mso-table-rspace:0;word-break:break-word"><tbody><tr><td class=3D"pa=
d" style=3D"padding-right:15px;padding-top:10px"><div style=3D"color:#6454d=
6;direction:ltr;font-family:&#39;Open Sans&#39;,&#39;Helvetica Neue&#39;,He=
lvetica,Arial,sans-serif;font-size:14px;font-weight:400;letter-spacing:0;li=
ne-height:150%;text-align:left;mso-line-height-alt:21px"><p style=3D"margin=
:0"><a href=3D"https://e.customeriomail.com/e/c/eyJlbWFpbF9pZCI6ImRnVHR5UWd=
EQVBMZ0dfSGdHd0dPeGZMODVtN2U1RklZRzNGS3JrRT0iLCJocmVmIjoiaHR0cHM6Ly93d3cudm=
lzaWx5LmFpL3JlbGVhc2Utbm90ZXMvcmVsZWFzZS1ub3RlLXYyLTYtYXByaWwtMjAyND91dG1fc=
291cmNlPWN1c3Rpb1x1MDAyNnV0bV9tZWRpdW09ZW1haWxcdTAwMjZ1dG1fY2FtcGFpZ249bWFy=
Y2gtd3JhcC11cFx1MDAyNnV0bV9jb250ZW50PXNsYWNrXHUwMDI2dXRtX3Rlcm09bGluayNzbWF=
ydC1jb21wb25lbnRzIiwiaW50ZXJuYWwiOiJlZGM5MDgwZmExMjVmMmUwMWIiLCJsaW5rX2lkIj=
oxMTI2fQ/d66493c3eef54da7b79b6963a6335418a20208c44c9d1cd15398642c0319e807" =
target=3D"_blank" style=3D"text-decoration: none; color: #6454d6;" rel=3D"n=
oopener">Watch demo =E2=86=92</a></p></div></td></tr></tbody></table></div>=
</td></tr></tbody></table></td></tr></tbody></table><table class=3D"row row=
-10" align=3D"center" width=3D"100%" border=3D"0" cellpadding=3D"0" cellspa=
cing=3D"0" role=3D"presentation" style=3D"mso-table-lspace:0;mso-table-rspa=
ce:0;background-color:#f1ecff"><tbody><tr><td><table class=3D"row-content s=
tack" align=3D"center" border=3D"0" cellpadding=3D"0" cellspacing=3D"0" rol=
e=3D"presentation" style=3D"mso-table-lspace:0;mso-table-rspace:0;backgroun=
d-color:#fff;border-radius:0;color:#000;width:740px;margin:0 auto" width=3D=
"740"><tbody><tr class=3D"reverse"><td class=3D"column column-1 first" widt=
h=3D"33.333333333333336%" style=3D"mso-table-lspace:0;mso-table-rspace:0;fo=
nt-weight:400;text-align:left;padding-bottom:10px;padding-left:60px;padding=
-right:20px;padding-top:10px;vertical-align:middle;border-top:0;border-righ=
t:0;border-bottom:0;border-left:0"><div class=3D"border"><table class=3D"im=
age_block block-1" width=3D"100%" border=3D"0" cellpadding=3D"0" cellspacin=
g=3D"0" role=3D"presentation" style=3D"mso-table-lspace:0;mso-table-rspace:=
0"><tbody><tr><td class=3D"pad" style=3D"width:100%"><div class=3D"alignmen=
t" align=3D"left" style=3D"line-height:10px"><div class=3D"fullWidth" style=
=3D"max-width:166.667px"><a href=3D"https://e.customeriomail.com/e/c/eyJlbW=
FpbF9pZCI6ImRnVHR5UWdEQVBMZ0dfSGdHd0dPeGZMODVtN2U1RklZRzNGS3JrRT0iLCJocmVmI=
joiaHR0cHM6Ly93d3cudmlzaWx5LmFpL3JlbGVhc2Utbm90ZXMvcmVsZWFzZS1ub3RlLXYyLTYt=
YXByaWwtMjAyND91dG1fc291cmNlPWN1c3Rpb1x1MDAyNnV0bV9tZWRpdW09ZW1haWxcdTAwMjZ=
1dG1fY2FtcGFpZ249bWFyY2gtd3JhcC11cFx1MDAyNnV0bV9jb250ZW50PWRpYWdyYW0tbGlicm=
FyeVx1MDAyNnV0bV90ZXJtPWxpbmsjZGlhZ3JhbS1saWJyYXJ5IiwiaW50ZXJuYWwiOiJlZGM5M=
DgwZmExMjVmMmUwMWIiLCJsaW5rX2lkIjoxMTI3fQ/607f810198a970f5bcf8ac4c97f880c91=
234f4435812c1f4e5117c5fc130341d" target=3D"_blank" style=3D"outline:none" t=
abindex=3D"-1"><img src=3D"https://userimg-assets.customeriomail.com/images=
/client-env-140525/1712639921177_Mar-wrap-up-4_01HV0MPK4WT3NKS8P83Q9ZE1TZ.p=
ng" style=3D"display:block;height:auto;border:0;width:100%" width=3D"166.66=
7" height=3D"auto"/></a></div></div></td></tr></tbody></table></div></td><t=
d class=3D"column column-2 last" width=3D"66.66666666666667%" style=3D"mso-=
table-lspace:0;mso-table-rspace:0;font-weight:400;text-align:left;padding-b=
ottom:5px;padding-left:20px;padding-right:40px;padding-top:5px;vertical-ali=
gn:middle;border-top:0;border-right:0;border-bottom:0;border-left:0"><div c=
lass=3D"border"><table class=3D"paragraph_block block-1" width=3D"100%" bor=
der=3D"0" cellpadding=3D"0" cellspacing=3D"0" role=3D"presentation" style=
=3D"mso-table-lspace:0;mso-table-rspace:0;word-break:break-word"><tbody><tr=
><td class=3D"pad" style=3D"padding-bottom:10px"><div style=3D"color:#6454d=
6;direction:ltr;font-family:&#39;Open Sans&#39;,&#39;Helvetica Neue&#39;,He=
lvetica,Arial,sans-serif;font-size:14px;font-weight:700;letter-spacing:0;li=
ne-height:150%;text-align:left;mso-line-height-alt:21px"><p style=3D"margin=
:0">Enjoy a Bigger &amp; Better Diagram Library</p></div></td></tr></tbody>=
</table><table class=3D"paragraph_block block-2" width=3D"100%" border=3D"0=
" cellpadding=3D"0" cellspacing=3D"0" role=3D"presentation" style=3D"mso-ta=
ble-lspace:0;mso-table-rspace:0;word-break:break-word"><tbody><tr><td class=
=3D"pad" style=3D"padding-right:15px"><div style=3D"color:#1a1a1a;direction=
:ltr;font-family:&#39;Open Sans&#39;,&#39;Helvetica Neue&#39;,Helvetica,Ari=
al,sans-serif;font-size:14px;font-weight:400;letter-spacing:0;line-height:1=
50%;text-align:left;mso-line-height-alt:21px"><p style=3D"margin:0">
We&#39;ve added many more brainstorming and diagram templates for various u=
se cases, such as user flows, sitemaps, project planning, product analysis,=
 meeting minutes, and more.</p></div></td></tr></tbody></table><table class=
=3D"paragraph_block block-3" width=3D"100%" border=3D"0" cellpadding=3D"0" =
cellspacing=3D"0" role=3D"presentation" style=3D"mso-table-lspace:0;mso-tab=
le-rspace:0;word-break:break-word"><tbody><tr><td class=3D"pad" style=3D"pa=
dding-right:15px;padding-top:10px"><div style=3D"color:#6454d6;direction:lt=
r;font-family:&#39;Open Sans&#39;,&#39;Helvetica Neue&#39;,Helvetica,Arial,=
sans-serif;font-size:14px;font-weight:400;letter-spacing:0;line-height:150%=
;text-align:left;mso-line-height-alt:21px"><p style=3D"margin:0"><a href=3D=
"https://e.customeriomail.com/e/c/eyJlbWFpbF9pZCI6ImRnVHR5UWdEQVBMZ0dfSGdHd=
0dPeGZMODVtN2U1RklZRzNGS3JrRT0iLCJocmVmIjoiaHR0cHM6Ly93d3cudmlzaWx5LmFpL3Jl=
bGVhc2Utbm90ZXMvcmVsZWFzZS1ub3RlLXYyLTYtYXByaWwtMjAyND91dG1fc291cmNlPWN1c3R=
pb1x1MDAyNnV0bV9tZWRpdW09ZW1haWxcdTAwMjZ1dG1fY2FtcGFpZ249bWFyY2gtd3JhcC11cF=
x1MDAyNnV0bV9jb250ZW50PWRpYWdyYW0tbGlicmFyeVx1MDAyNnV0bV90ZXJtPWxpbmsjZGlhZ=
3JhbS1saWJyYXJ5IiwiaW50ZXJuYWwiOiJlZGM5MDgwZmExMjVmMmUwMWIiLCJsaW5rX2lkIjox=
MTI3fQ/607f810198a970f5bcf8ac4c97f880c91234f4435812c1f4e5117c5fc130341d" ta=
rget=3D"_blank" style=3D"text-decoration: none; color: #6454d6;" rel=3D"noo=
pener">Explore our new templates =E2=86=92</a></p></div></td></tr></tbody><=
/table></div></td></tr></tbody></table></td></tr></tbody></table><table cla=
ss=3D"row row-11" align=3D"center" width=3D"100%" border=3D"0" cellpadding=
=3D"0" cellspacing=3D"0" role=3D"presentation" style=3D"mso-table-lspace:0;=
mso-table-rspace:0;background-color:#f1ecff"><tbody><tr><td><table class=3D=
"row-content stack" align=3D"center" border=3D"0" cellpadding=3D"0" cellspa=
cing=3D"0" role=3D"presentation" style=3D"mso-table-lspace:0;mso-table-rspa=
ce:0;background-color:#fff;border-radius:0;color:#000;width:740px;margin:0 =
auto" width=3D"740"><tbody><tr class=3D"reverse"><td class=3D"column column=
-1 first" width=3D"33.333333333333336%" style=3D"mso-table-lspace:0;mso-tab=
le-rspace:0;font-weight:400;text-align:left;padding-bottom:10px;padding-lef=
t:60px;padding-right:20px;padding-top:10px;vertical-align:middle;border-top=
:0;border-right:0;border-bottom:0;border-left:0"><div class=3D"border"><tab=
le class=3D"image_block block-1" width=3D"100%" border=3D"0" cellpadding=3D=
"0" cellspacing=3D"0" role=3D"presentation" style=3D"mso-table-lspace:0;mso=
-table-rspace:0"><tbody><tr><td class=3D"pad" style=3D"width:100%"><div cla=
ss=3D"alignment" align=3D"left" style=3D"line-height:10px"><div class=3D"fu=
llWidth" style=3D"max-width:166.667px"><a href=3D"https://e.customeriomail.=
com/e/c/eyJlbWFpbF9pZCI6ImRnVHR5UWdEQVBMZ0dfSGdHd0dPeGZMODVtN2U1RklZRzNGS3J=
rRT0iLCJocmVmIjoiaHR0cHM6Ly93d3cudmlzaWx5LmFpL3JlbGVhc2Utbm90ZXMvcmVsZWFzZS=
1ub3RlLXYyLTYtYXByaWwtMjAyND91dG1fc291cmNlPWN1c3Rpb1x1MDAyNnV0bV9tZWRpdW09Z=
W1haWxcdTAwMjZ1dG1fY2FtcGFpZ249bWFyY2gtd3JhcC11cFx1MDAyNnV0bV9jb250ZW50PXNs=
YWNrXHUwMDI2dXRtX3Rlcm09bGluayNpbnZpdGUtdGVhbW1hdGVzIiwiaW50ZXJuYWwiOiJlZGM=
5MDgwZmExMjVmMmUwMWIiLCJsaW5rX2lkIjoxMTI4fQ/8c783ec94bb0fc757bd3a5826c91b28=
b556b3e16843d029955178997765b2eea" target=3D"_blank" style=3D"outline:none"=
 tabindex=3D"-1"><img src=3D"https://userimg-assets.customeriomail.com/imag=
es/client-env-140525/1712639919735_Mar-wrap-up-3_01HV0MPHR368RVVA7YVBR7T25E=
.png" style=3D"display:block;height:auto;border:0;width:100%" width=3D"166.=
667" height=3D"auto"/></a></div></div></td></tr></tbody></table>
</div></td><td class=3D"column column-2 last" width=3D"66.66666666666667%" =
style=3D"mso-table-lspace:0;mso-table-rspace:0;font-weight:400;text-align:l=
eft;padding-bottom:5px;padding-left:20px;padding-right:40px;padding-top:5px=
;vertical-align:middle;border-top:0;border-right:0;border-bottom:0;border-l=
eft:0"><div class=3D"border"><table class=3D"paragraph_block block-1" width=
=3D"100%" border=3D"0" cellpadding=3D"0" cellspacing=3D"0" role=3D"presenta=
tion" style=3D"mso-table-lspace:0;mso-table-rspace:0;word-break:break-word"=
><tbody><tr><td class=3D"pad" style=3D"padding-bottom:10px"><div style=3D"c=
olor:#6454d6;direction:ltr;font-family:&#39;Open Sans&#39;,&#39;Helvetica N=
eue&#39;,Helvetica,Arial,sans-serif;font-size:14px;font-weight:700;letter-s=
pacing:0;line-height:150%;text-align:left;mso-line-height-alt:21px"><p styl=
e=3D"margin:0">Collaborate Easier Than Ever</p></div></td></tr></tbody></ta=
ble><table class=3D"paragraph_block block-2" width=3D"100%" border=3D"0" ce=
llpadding=3D"0" cellspacing=3D"0" role=3D"presentation" style=3D"mso-table-=
lspace:0;mso-table-rspace:0;word-break:break-word"><tbody><tr><td class=3D"=
pad" style=3D"padding-right:50px"><div style=3D"color:#1a1a1a;direction:ltr=
;font-family:&#39;Open Sans&#39;,&#39;Helvetica Neue&#39;,Helvetica,Arial,s=
ans-serif;font-size:14px;font-weight:400;letter-spacing:0;line-height:150%;=
text-align:left;mso-line-height-alt:21px"><p style=3D"margin:0">We=E2=80=99=
ve redesigned the =E2=80=9CInvite members to Workspace=E2=80=9D experience =
to be more intuitive and user-friendly.=C2=A0</p>
</div></td></tr></tbody></table><table class=3D"paragraph_block block-3" wi=
dth=3D"100%" border=3D"0" cellpadding=3D"0" cellspacing=3D"0" role=3D"prese=
ntation" style=3D"mso-table-lspace:0;mso-table-rspace:0;word-break:break-wo=
rd"><tbody><tr><td class=3D"pad" style=3D"padding-right:15px;padding-top:10=
px"><div style=3D"color:#6454d6;direction:ltr;font-family:&#39;Open Sans&#3=
9;,&#39;Helvetica Neue&#39;,Helvetica,Arial,sans-serif;font-size:14px;font-=
weight:400;letter-spacing:0;line-height:150%;text-align:left;mso-line-heigh=
t-alt:21px"><p style=3D"margin:0"><a href=3D"https://e.customeriomail.com/e=
/c/eyJlbWFpbF9pZCI6ImRnVHR5UWdEQVBMZ0dfSGdHd0dPeGZMODVtN2U1RklZRzNGS3JrRT0i=
LCJocmVmIjoiaHR0cHM6Ly93d3cudmlzaWx5LmFpL3JlbGVhc2Utbm90ZXMvcmVsZWFzZS1ub3R=
lLXYyLTYtYXByaWwtMjAyND91dG1fc291cmNlPWN1c3Rpb1x1MDAyNnV0bV9tZWRpdW09ZW1haW=
xcdTAwMjZ1dG1fY2FtcGFpZ249bWFyY2gtd3JhcC11cFx1MDAyNnV0bV9jb250ZW50PXNsYWNrX=
HUwMDI2dXRtX3Rlcm09bGluayNpbnZpdGUtdGVhbW1hdGVzIiwiaW50ZXJuYWwiOiJlZGM5MDgw=
ZmExMjVmMmUwMWIiLCJsaW5rX2lkIjoxMTI4fQ/8c783ec94bb0fc757bd3a5826c91b28b556b=
3e16843d029955178997765b2eea" target=3D"_blank" style=3D"text-decoration: n=
one; color: #6454d6;" rel=3D"noopener">Show me now =E2=86=92</a></p></div><=
/td></tr></tbody></table></div></td></tr></tbody></table></td></tr></tbody>=
</table><table class=3D"row row-12" align=3D"center" width=3D"100%" border=
=3D"0" cellpadding=3D"0" cellspacing=3D"0" role=3D"presentation" style=3D"m=
so-table-lspace:0;mso-table-rspace:0;background-color:#f1ecff"><tbody><tr><=
td><table class=3D"row-content stack" align=3D"center" border=3D"0" cellpad=
ding=3D"0" cellspacing=3D"0" role=3D"presentation" style=3D"mso-table-lspac=
e:0;mso-table-rspace:0;background-color:#fff;border-radius:0;color:#000;wid=
th:740px;margin:0 auto" width=3D"740"><tbody><tr><td class=3D"column column=
-1" width=3D"100%" style=3D"mso-table-lspace:0;mso-table-rspace:0;font-weig=
ht:400;text-align:left;padding-bottom:10px;padding-left:60px;padding-right:=
60px;padding-top:35px;vertical-align:top;border-top:0;border-right:0;border=
-bottom:0;border-left:0"><table class=3D"image_block block-1" width=3D"100%=
" border=3D"0" cellpadding=3D"0" cellspacing=3D"0" role=3D"presentation" st=
yle=3D"mso-table-lspace:0;mso-table-rspace:0"><tbody><tr><td class=3D"pad" =
style=3D"width:100%;padding-right:0;padding-left:0"><div class=3D"alignment=
" align=3D"left" style=3D"line-height:10px"><div class=3D"fullWidth" style=
=3D"max-width:248px"><img src=3D"https://userimg-assets.customeriomail.com/=
images/client-env-140525/1712640113551_Group%201321314354-min_01HV0MWF0VHER=
3F876D4K3N4AW.png" style=3D"display:block;height:auto;border:0;width:100%" =
width=3D"248" height=3D"auto"/></div></div></td></tr></tbody></table></td><=
/tr></tbody></table></td></tr></tbody></table><table class=3D"row row-13" a=
lign=3D"center" width=3D"100%" border=3D"0" cellpadding=3D"0" cellspacing=
=3D"0" role=3D"presentation" style=3D"mso-table-lspace:0;mso-table-rspace:0=
;background-color:#f1ecff"><tbody><tr><td><table class=3D"row-content stack=
" align=3D"center" border=3D"0" cellpadding=3D"0" cellspacing=3D"0" role=3D=
"presentation" style=3D"mso-table-lspace:0;mso-table-rspace:0;background-co=
lor:#fff;border-radius:0;color:#000;width:740px;margin:0 auto" width=3D"740=
"><tbody><tr class=3D"reverse"><td class=3D"column column-1 first" width=3D=
"33.333333333333336%" style=3D"mso-table-lspace:0;mso-table-rspace:0;font-w=
eight:400;text-align:left;padding-bottom:10px;padding-left:60px;padding-rig=
ht:20px;padding-top:10px;vertical-align:middle;border-top:0;border-right:0;=
border-bottom:0;border-left:0"><div class=3D"border"><table class=3D"image_=
block block-1" width=3D"100%" border=3D"0" cellpadding=3D"0" cellspacing=3D=
"0" role=3D"presentation" style=3D"mso-table-lspace:0;mso-table-rspace:0"><=
tbody><tr><td class=3D"pad" style=3D"width:100%"><div class=3D"alignment" a=
lign=3D"left" style=3D"line-height:10px"><div class=3D"fullWidth" style=3D"=
max-width:166.667px"><a href=3D"https://e.customeriomail.com/e/c/eyJlbWFpbF=
9pZCI6ImRnVHR5UWdEQVBMZ0dfSGdHd0dPeGZMODVtN2U1RklZRzNGS3JrRT0iLCJocmVmIjoia=
HR0cHM6Ly9hcHAudmlzaWx5LmFpL3RyeS90ZXh0X3RvX2RpYWdyYW0_dXRtX3NvdXJjZT1jdXN0=
aW9cdTAwMjZ1dG1fbWVkaXVtPWVtYWlsXHUwMDI2dXRtX2NhbXBhaWduPW1hcmNoLXdyYXAtdXB=
cdTAwMjZ1dG1fY29udGVudD10ZXh0LXRvLWRpYWdyYW1cdTAwMjZ1dG1fdGVybT1saW5rIiwiaW=
50ZXJuYWwiOiJlZGM5MDgwZmExMjVmMmUwMWIiLCJsaW5rX2lkIjoxMTI5fQ/30ca7827908662=
147feaa53ae078a6b332212473838004b0024f80bd0045cc60" target=3D"_blank" style=
=3D"outline:none" tabindex=3D"-1"><img src=3D"https://userimg-assets.custom=
eriomail.com/images/client-env-140525/1712639955901_Mar-wrap-up-9_01HV0MQN2=
2FWN09JZEMXWWT37G.png" style=3D"display:block;height:auto;border:0;width:10=
0%" width=3D"166.667" height=3D"auto"/></a></div></div></td></tr></tbody></=
table></div></td><td class=3D"column column-2 last" width=3D"66.66666666666=
667%" style=3D"mso-table-lspace:0;mso-table-rspace:0;font-weight:400;text-a=
lign:left;padding-bottom:5px;padding-left:20px;padding-right:40px;padding-t=
op:5px;vertical-align:middle;border-top:0;border-right:0;border-bottom:0;bo=
rder-left:0"><div class=3D"border"><table class=3D"paragraph_block block-1"=
 width=3D"100%" border=3D"0" cellpadding=3D"0" cellspacing=3D"0" role=3D"pr=
esentation" style=3D"mso-table-lspace:0;mso-table-rspace:0;word-break:break=
-word"><tbody><tr><td class=3D"pad" style=3D"padding-bottom:10px"><div styl=
e=3D"color:#6454d6;direction:ltr;font-family:&#39;Open Sans&#39;,&#39;Helve=
tica Neue&#39;,Helvetica,Arial,sans-serif;font-size:14px;font-weight:700;le=
tter-spacing:0;line-height:150%;text-align:left;mso-line-height-alt:21px"><=
p style=3D"margin:0">Make Diagramming Effortless with Text to Diagram</p></=
div></td></tr></tbody></table><table class=3D"paragraph_block block-2" widt=
h=3D"100%" border=3D"0" cellpadding=3D"0" cellspacing=3D"0" role=3D"present=
ation" style=3D"mso-table-lspace:0;mso-table-rspace:0;word-break:break-word=
"><tbody><tr><td class=3D"pad" style=3D"padding-right:30px"><div style=3D"c=
olor:#1a1a1a;direction:ltr;font-family:&#39;Open Sans&#39;,&#39;Helvetica N=
eue&#39;,Helvetica,Arial,sans-serif;font-size:14px;font-weight:400;letter-s=
pacing:0;line-height:150%;text-align:left;mso-line-height-alt:21px"><p styl=
e=3D"margin:0">Don=E2=80=99t miss out the AI feature: <strong>Text to Diagr=
am</strong> =E2=9C=A8. Experience the simplicity of turning text into visua=
ls with Text to Diagram.=C2=A0</p></div></td></tr></tbody></table><table cl=
ass=3D"paragraph_block block-3" width=3D"100%" border=3D"0" cellpadding=3D"=
0" cellspacing=3D"0" role=3D"presentation" style=3D"mso-table-lspace:0;mso-=
table-rspace:0;word-break:break-word"><tbody><tr><td class=3D"pad" style=3D=
"padding-right:15px;padding-top:10px"><div style=3D"color:#6454d6;direction=
:ltr;font-family:&#39;Open Sans&#39;,&#39;Helvetica Neue&#39;,Helvetica,Ari=
al,sans-serif;font-size:14px;font-weight:400;letter-spacing:0;line-height:1=
50%;text-align:left;mso-line-height-alt:21px"><p style=3D"margin:0">
<a href=3D"https://e.customeriomail.com/e/c/eyJlbWFpbF9pZCI6ImRnVHR5UWdEQVB=
MZ0dfSGdHd0dPeGZMODVtN2U1RklZRzNGS3JrRT0iLCJocmVmIjoiaHR0cHM6Ly9hcHAudmlzaW=
x5LmFpL3RyeS90ZXh0X3RvX2RpYWdyYW0_dXRtX3NvdXJjZT1jdXN0aW9cdTAwMjZ1dG1fbWVka=
XVtPWVtYWlsXHUwMDI2dXRtX2NhbXBhaWduPW1hcmNoLXdyYXAtdXBcdTAwMjZ1dG1fY29udGVu=
dD10ZXh0LXRvLWRpYWdyYW1cdTAwMjZ1dG1fdGVybT1saW5rIiwiaW50ZXJuYWwiOiJlZGM5MDg=
wZmExMjVmMmUwMWIiLCJsaW5rX2lkIjoxMTI5fQ/30ca7827908662147feaa53ae078a6b3322=
12473838004b0024f80bd0045cc60" target=3D"_blank" style=3D"text-decoration: =
none; color: #6454d6;" rel=3D"noopener">Let AI streamline your design proce=
ss =E2=86=92</a></p></div></td></tr></tbody></table></div></td></tr></tbody=
></table></td></tr></tbody></table><table class=3D"row row-14" align=3D"cen=
ter" width=3D"100%" border=3D"0" cellpadding=3D"0" cellspacing=3D"0" role=
=3D"presentation" style=3D"mso-table-lspace:0;mso-table-rspace:0;background=
-color:#f1ecff"><tbody><tr><td><table class=3D"row-content stack" align=3D"=
center" border=3D"0" cellpadding=3D"0" cellspacing=3D"0" role=3D"presentati=
on" style=3D"mso-table-lspace:0;mso-table-rspace:0;background-color:#fff;bo=
rder-radius:0;color:#000;width:740px;margin:0 auto" width=3D"740"><tbody><t=
r><td class=3D"column column-1" width=3D"100%" style=3D"mso-table-lspace:0;=
mso-table-rspace:0;font-weight:400;text-align:left;padding-bottom:10px;padd=
ing-left:60px;padding-right:60px;padding-top:35px;vertical-align:top;border=
-top:0;border-right:0;border-bottom:0;border-left:0"><table class=3D"image_=
block block-1" width=3D"100%" border=3D"0" cellpadding=3D"0" cellspacing=3D=
"0" role=3D"presentation" style=3D"mso-table-lspace:0;mso-table-rspace:0"><=
tbody><tr><td class=3D"pad" style=3D"width:100%;padding-right:0;padding-lef=
t:0"><div class=3D"alignment" align=3D"left" style=3D"line-height:10px"><di=
v class=3D"fullWidth" style=3D"max-width:248px"><img src=3D"https://userimg=
-assets.customeriomail.com/images/client-env-140525/1709572462858_Group%201=
321314347-min_01HR57B6ECXT139KX568EYVSS8.png" style=3D"display:block;height=
:auto;border:0;width:100%" width=3D"248" height=3D"auto"/></div></div></td>=
</tr></tbody></table></td></tr></tbody></table></td></tr></tbody></table><t=
able class=3D"row row-15" align=3D"center" width=3D"100%" border=3D"0" cell=
padding=3D"0" cellspacing=3D"0" role=3D"presentation" style=3D"mso-table-ls=
pace:0;mso-table-rspace:0;background-color:#f1ecff"><tbody><tr><td><table c=
lass=3D"row-content stack" align=3D"center" border=3D"0" cellpadding=3D"0" =
cellspacing=3D"0" role=3D"presentation" style=3D"mso-table-lspace:0;mso-tab=
le-rspace:0;background-color:#fff;border-radius:0;color:#000;width:740px;ma=
rgin:0 auto" width=3D"740"><tbody><tr class=3D"reverse"><td class=3D"column=
 column-1 first" width=3D"33.333333333333336%" style=3D"mso-table-lspace:0;=
mso-table-rspace:0;font-weight:400;text-align:left;padding-bottom:10px;padd=
ing-left:60px;padding-right:20px;padding-top:10px;vertical-align:middle;bor=
der-top:0;border-right:0;border-bottom:0;border-left:0"><div class=3D"borde=
r"><table class=3D"image_block block-1" width=3D"100%" border=3D"0" cellpad=
ding=3D"0" cellspacing=3D"0" role=3D"presentation" style=3D"mso-table-lspac=
e:0;mso-table-rspace:0"><tbody><tr><td class=3D"pad" style=3D"width:100%"><=
div class=3D"alignment" align=3D"left" style=3D"line-height:10px"><div clas=
s=3D"fullWidth" style=3D"max-width:166.667px"><a href=3D"https://e.customer=
iomail.com/e/c/eyJlbWFpbF9pZCI6ImRnVHR5UWdEQVBMZ0dfSGdHd0dPeGZMODVtN2U1RklZ=
RzNGS3JrRT0iLCJocmVmIjoiaHR0cHM6Ly93d3cueW91dHViZS5jb20vcGxheWxpc3Q_bGlzdD1=
QTDEyczVkM3kxeENuSlExdzhkM1FzRExNOUpuWWkwWi1iIiwiaW50ZXJuYWwiOiJlZGM5MDgwZm=
ExMjVmMmUwMWIiLCJsaW5rX2lkIjoxMTMwfQ/26df2e2c6aa509e0c99b5082942f0e0d378aa5=
8f0dfd1cb97d10ca9059610996" target=3D"_blank" style=3D"outline:none" tabind=
ex=3D"-1"><img src=3D"https://userimg-assets.customeriomail.com/images/clie=
nt-env-140525/1712639953818_Mar-wrap-up-8_01HV0MQKEX1V0Y82S3V5A6RJ91.png" s=
tyle=3D"display:block;height:auto;border:0;width:100%" width=3D"166.667" he=
ight=3D"auto"/></a></div></div></td></tr></tbody></table></div></td><td cla=
ss=3D"column column-2 last" width=3D"66.66666666666667%" style=3D"mso-table=
-lspace:0;mso-table-rspace:0;font-weight:400;text-align:left;padding-bottom=
:5px;padding-left:20px;padding-right:40px;padding-top:5px;vertical-align:mi=
ddle;border-top:0;border-right:0;border-bottom:0;border-left:0"><div class=
=3D"border"><table class=3D"paragraph_block block-1" width=3D"100%" border=
=3D"0" cellpadding=3D"0" cellspacing=3D"0" role=3D"presentation" style=3D"m=
so-table-lspace:0;mso-table-rspace:0;word-break:break-word"><tbody><tr><td =
class=3D"pad" style=3D"padding-bottom:10px"><div style=3D"color:#6454d6;dir=
ection:ltr;font-family:&#39;Open Sans&#39;,&#39;Helvetica Neue&#39;,Helveti=
ca,Arial,sans-serif;font-size:14px;font-weight:700;letter-spacing:0;line-he=
ight:150%;text-align:left;mso-line-height-alt:21px"><p style=3D"margin:0">L=
earn About AI Trends in Product Management</p></div></td></tr></tbody></tab=
le><table class=3D"paragraph_block block-2" width=3D"100%" border=3D"0" cel=
lpadding=3D"0" cellspacing=3D"0" role=3D"presentation" style=3D"mso-table-l=
space:0;mso-table-rspace:0;word-break:break-word"><tbody><tr><td class=3D"p=
ad" style=3D"padding-right:30px"><div style=3D"color:#1a1a1a;direction:ltr;=
font-family:&#39;Open Sans&#39;,&#39;Helvetica Neue&#39;,Helvetica,Arial,sa=
ns-serif;font-size:14px;font-weight:400;letter-spacing:0;line-height:150%;t=
ext-align:left;mso-line-height-alt:21px"><p style=3D"margin:0">
As AI capabilities advance, how will the role of product managers evolve? W=
hat new responsibilities will they take on? How can PMs take advantage of A=
I to build better products? Learn more from our audio blog series!</p></div=
></td></tr></tbody></table><table class=3D"paragraph_block block-3" width=
=3D"100%" border=3D"0" cellpadding=3D"0" cellspacing=3D"0" role=3D"presenta=
tion" style=3D"mso-table-lspace:0;mso-table-rspace:0;word-break:break-word"=
><tbody><tr><td class=3D"pad" style=3D"padding-right:15px;padding-top:10px"=
><div style=3D"color:#6454d6;direction:ltr;font-family:&#39;Open Sans&#39;,=
&#39;Helvetica Neue&#39;,Helvetica,Arial,sans-serif;font-size:14px;font-wei=
ght:400;letter-spacing:0;line-height:150%;text-align:left;mso-line-height-a=
lt:21px"><p style=3D"margin:0"><a href=3D"https://e.customeriomail.com/e/c/=
eyJlbWFpbF9pZCI6ImRnVHR5UWdEQVBMZ0dfSGdHd0dPeGZMODVtN2U1RklZRzNGS3JrRT0iLCJ=
ocmVmIjoiaHR0cHM6Ly93d3cueW91dHViZS5jb20vcGxheWxpc3Q_bGlzdD1QTDEyczVkM3kxeE=
NuSlExdzhkM1FzRExNOUpuWWkwWi1iIiwiaW50ZXJuYWwiOiJlZGM5MDgwZmExMjVmMmUwMWIiL=
CJsaW5rX2lkIjoxMTMwfQ/26df2e2c6aa509e0c99b5082942f0e0d378aa58f0dfd1cb97d10c=
a9059610996" target=3D"_blank" style=3D"text-decoration: none; color: #6454=
d6;" rel=3D"noopener">Check out the blog series =E2=86=92</a></p></div></td=
></tr></tbody></table></div></td></tr></tbody></table></td></tr></tbody></t=
able><table class=3D"row row-16 mobile_hide" align=3D"center" width=3D"100%=
" border=3D"0" cellpadding=3D"0" cellspacing=3D"0" role=3D"presentation" st=
yle=3D"mso-table-lspace:0;mso-table-rspace:0;background-color:#f1ecff"><tbo=
dy><tr><td><table class=3D"row-content stack" align=3D"center" border=3D"0"=
 cellpadding=3D"0" cellspacing=3D"0" role=3D"presentation" style=3D"mso-tab=
le-lspace:0;mso-table-rspace:0;background-color:#fff;color:#000;border-radi=
us:0 0 12px 12px;width:740px;margin:0 auto" width=3D"740"><tbody><tr><td cl=
ass=3D"column column-1" width=3D"100%" style=3D"mso-table-lspace:0;mso-tabl=
e-rspace:0;font-weight:400;text-align:left;padding-bottom:50px;padding-left=
:40px;padding-right:40px;padding-top:50px;vertical-align:top;border-top:0;b=
order-right:0;border-bottom:0;border-left:0"><table class=3D"button_block b=
lock-1" width=3D"100%" border=3D"0" cellpadding=3D"0" cellspacing=3D"0" rol=
e=3D"presentation" style=3D"mso-table-lspace:0;mso-table-rspace:0"><tbody><=
tr><td class=3D"pad" style=3D"text-align:center"><div class=3D"alignment" a=
lign=3D"center"><!--[if mso]>
<v:roundrect xmlns:v=3D"urn:schemas-microsoft-com:vml" xmlns:w=3D"urn:schem=
as-microsoft-com:office:word" href=3D"https://e.customeriomail.com/e/c/eyJl=
bWFpbF9pZCI6ImRnVHR5UWdEQVBMZ0dfSGdHd0dPeGZMODVtN2U1RklZRzNGS3JrRT0iLCJocmV=
mIjoiaHR0cHM6Ly9hcHAudmlzaWx5LmFpLz91dG1fc291cmNlPWN1c3Rpb1x1MDAyNnV0bV9tZW=
RpdW09ZW1haWxcdTAwMjZ1dG1fY2FtcGFpZ249bWFyY2gtd3JhcC11cFx1MDAyNnV0bV9jb250Z=
W50PWJhY2stdG8tYXBwXHUwMDI2dXRtX3Rlcm09Y3RhLWJ1dHRvbiIsImludGVybmFsIjoiZWRj=
OTA4MGZhMTI1ZjJlMDFiIiwibGlua19pZCI6MTEzMX0/7aeaa6d1acda8766e3be73747581d94=
0b4ada5ce5db4ec89b3c623971d24b34a" style=3D"height:44px;width:202px;v-text-=
anchor:middle;" arcsize=3D"19%" stroke=3D"false" fillcolor=3D"#6454d6">
<w:anchorlock/>
<v:textbox inset=3D"0px,0px,0px,0px">
<center style=3D"color:#ffffff; font-family:Arial, sans-serif; font-size:14=
px">
<![endif]-->
<a href=3D"https://e.customeriomail.com/e/c/eyJlbWFpbF9pZCI6ImRnVHR5UWdEQVB=
MZ0dfSGdHd0dPeGZMODVtN2U1RklZRzNGS3JrRT0iLCJocmVmIjoiaHR0cHM6Ly9hcHAudmlzaW=
x5LmFpLz91dG1fc291cmNlPWN1c3Rpb1x1MDAyNnV0bV9tZWRpdW09ZW1haWxcdTAwMjZ1dG1fY=
2FtcGFpZ249bWFyY2gtd3JhcC11cFx1MDAyNnV0bV9jb250ZW50PWJhY2stdG8tYXBwXHUwMDI2=
dXRtX3Rlcm09Y3RhLWJ1dHRvbiIsImludGVybmFsIjoiZWRjOTA4MGZhMTI1ZjJlMDFiIiwibGl=
ua19pZCI6MTEzMX0/7aeaa6d1acda8766e3be73747581d940b4ada5ce5db4ec89b3c623971d=
24b34a" target=3D"_blank" style=3D"text-decoration:none;display:inline-bloc=
k;color:#ffffff;background-color:#6454d6;border-radius:8px;width:auto;borde=
r-top:0px solid transparent;font-weight:400;border-right:0px solid transpar=
ent;border-bottom:0px solid transparent;border-left:0px solid transparent;p=
adding-top:8px;padding-bottom:8px;font-family:&#39;Open Sans&#39;, &#39;Hel=
vetica Neue&#39;, Helvetica, Arial, sans-serif;font-size:14px;text-align:ce=
nter;mso-border-alt:none;word-break:keep-all;"><span style=3D"padding-left:=
14px;padding-right:14px;font-size:14px;display:inline-block;letter-spacing:=
normal;"><span style=3D"word-break: break-word; line-height: 28px;"><strong=
>Head to the
design space</strong></span></span></a>
<!--[if mso]></center></v:textbox></v:roundrect><![endif]--></div></td></tr=
></tbody></table></td></tr></tbody></table></td></tr></tbody></table><table=
 class=3D"row row-17 desktop_hide" align=3D"center" width=3D"100%" border=
=3D"0" cellpadding=3D"0" cellspacing=3D"0" role=3D"presentation" style=3D"m=
so-table-lspace:0;mso-table-rspace:0;mso-hide:all;display:none;max-height:0=
;overflow:hidden;background-color:#f1ecff"><tbody><tr><td><table class=3D"r=
ow-content stack" align=3D"center" border=3D"0" cellpadding=3D"0" cellspaci=
ng=3D"0" role=3D"presentation" style=3D"mso-table-lspace:0;mso-table-rspace=
:0;mso-hide:all;display:none;max-height:0;overflow:hidden;background-color:=
#fff;color:#000;border-radius:0 0 1px 1px;width:740px;margin:0 auto" width=
=3D"740"><tbody><tr><td class=3D"column column-1" width=3D"100%" style=3D"m=
so-table-lspace:0;mso-table-rspace:0;font-weight:400;text-align:left;paddin=
g-bottom:50px;padding-left:40px;padding-right:40px;padding-top:50px;vertica=
l-align:top;border-top:0;border-right:0;border-bottom:0;border-left:0">
<table class=3D"button_block block-1" width=3D"100%" border=3D"0" cellpaddi=
ng=3D"0" cellspacing=3D"0" role=3D"presentation" style=3D"mso-table-lspace:=
0;mso-table-rspace:0;mso-hide:all;display:none;max-height:0;overflow:hidden=
"><tbody><tr><td class=3D"pad" style=3D"text-align:center"><div class=3D"al=
ignment" align=3D"center"><!--[if mso]>
<v:roundrect xmlns:v=3D"urn:schemas-microsoft-com:vml" xmlns:w=3D"urn:schem=
as-microsoft-com:office:word" href=3D"https://e.customeriomail.com/e/c/eyJl=
bWFpbF9pZCI6ImRnVHR5UWdEQVBMZ0dfSGdHd0dPeGZMODVtN2U1RklZRzNGS3JrRT0iLCJocmV=
mIjoiaHR0cHM6Ly9hcHAudmlzaWx5LmFpLz91dG1fc291cmNlPWN1c3Rpb1x1MDAyNnV0bV9tZW=
RpdW09ZW1haWxcdTAwMjZ1dG1fY2FtcGFpZ249bWFyY2gtd3JhcC11cFx1MDAyNnV0bV9jb250Z=
W50PWJhY2stdG8tYXBwXHUwMDI2dXRtX3Rlcm09Y3RhLWJ1dHRvbiIsImludGVybmFsIjoiZWRj=
OTA4MGZhMTI1ZjJlMDFiIiwibGlua19pZCI6MTEzMX0/7aeaa6d1acda8766e3be73747581d94=
0b4ada5ce5db4ec89b3c623971d24b34a" style=3D"height:44px;width:202px;v-text-=
anchor:middle;" arcsize=3D"19%" stroke=3D"false" fillcolor=3D"#6454d6">
<w:anchorlock/>
<v:textbox inset=3D"0px,0px,0px,0px">
<center style=3D"color:#ffffff; font-family:Arial, sans-serif; font-size:14=
px">
<![endif]-->
<a href=3D"https://e.customeriomail.com/e/c/eyJlbWFpbF9pZCI6ImRnVHR5UWdEQVB=
MZ0dfSGdHd0dPeGZMODVtN2U1RklZRzNGS3JrRT0iLCJocmVmIjoiaHR0cHM6Ly9hcHAudmlzaW=
x5LmFpLz91dG1fc291cmNlPWN1c3Rpb1x1MDAyNnV0bV9tZWRpdW09ZW1haWxcdTAwMjZ1dG1fY=
2FtcGFpZ249bWFyY2gtd3JhcC11cFx1MDAyNnV0bV9jb250ZW50PWJhY2stdG8tYXBwXHUwMDI2=
dXRtX3Rlcm09Y3RhLWJ1dHRvbiIsImludGVybmFsIjoiZWRjOTA4MGZhMTI1ZjJlMDFiIiwibGl=
ua19pZCI6MTEzMX0/7aeaa6d1acda8766e3be73747581d940b4ada5ce5db4ec89b3c623971d=
24b34a" target=3D"_blank" style=3D"text-decoration:none;display:inline-bloc=
k;color:#ffffff;background-color:#6454d6;border-radius:8px;width:auto;borde=
r-top:0px solid transparent;font-weight:400;border-right:0px solid transpar=
ent;border-bottom:0px solid transparent;border-left:0px solid transparent;p=
adding-top:8px;padding-bottom:8px;font-family:&#39;Open Sans&#39;, &#39;Hel=
vetica Neue&#39;, Helvetica, Arial, sans-serif;font-size:14px;text-align:ce=
nter;mso-border-alt:none;word-break:keep-all;"><span style=3D"padding-left:=
14px;padding-right:14px;font-size:14px;display:inline-block;letter-spacing:=
normal;"><span style=3D"word-break: break-word; line-height: 28px;"><strong=
>Head to the
design space</strong></span></span></a>
<!--[if mso]></center></v:textbox></v:roundrect><![endif]--></div></td></tr=
></tbody></table></td></tr></tbody></table></td></tr></tbody></table><table=
 class=3D"row row-18 desktop_hide" align=3D"center" width=3D"100%" border=
=3D"0" cellpadding=3D"0" cellspacing=3D"0" role=3D"presentation" style=3D"m=
so-table-lspace:0;mso-table-rspace:0;mso-hide:all;display:none;max-height:0=
;overflow:hidden;background-color:#f1ecff"><tbody><tr><td><table class=3D"r=
ow-content stack" align=3D"center" border=3D"0" cellpadding=3D"0" cellspaci=
ng=3D"0" role=3D"presentation" style=3D"mso-table-lspace:0;mso-table-rspace=
:0;mso-hide:all;display:none;max-height:0;overflow:hidden;background-color:=
#fff;color:#000;width:740px;margin:0 auto" width=3D"740"><tbody><tr><td cla=
ss=3D"column column-1" width=3D"100%" style=3D"mso-table-lspace:0;mso-table=
-rspace:0;font-weight:400;text-align:left;padding-bottom:5px;padding-left:4=
0px;padding-right:40px;padding-top:5px;vertical-align:top;border-top:0;bord=
er-right:0;border-bottom:0;border-left:0"><table class=3D"paragraph_block b=
lock-1" width=3D"100%" border=3D"0" cellpadding=3D"0" cellspacing=3D"0" rol=
e=3D"presentation" style=3D"mso-table-lspace:0;mso-table-rspace:0;word-brea=
k:break-word;mso-hide:all;display:none;max-height:0;overflow:hidden"><tbody=
><tr><td class=3D"pad" style=3D"padding-bottom:10px;padding-left:10px;paddi=
ng-right:10px;padding-top:20px"><div style=3D"color:#12101a;direction:ltr;f=
ont-family:&#39;Open Sans&#39;,&#39;Helvetica Neue&#39;,Helvetica,Arial,san=
s-serif;font-size:12px;font-weight:400;letter-spacing:0;line-height:120%;te=
xt-align:center;mso-line-height-alt:14.399999999999999px"><p style=3D"margi=
n:0"><strong>Visily</strong>, AI-powered app wireframing &amp; prototyping<=
/p></div></td></tr></tbody></table><table class=3D"paragraph_block block-2"=
 width=3D"100%" border=3D"0" cellpadding=3D"10" cellspacing=3D"0" role=3D"p=
resentation" style=3D"mso-table-lspace:0;mso-table-rspace:0;word-break:brea=
k-word;mso-hide:all;display:none;max-height:0;overflow:hidden"><tbody><tr><=
td class=3D"pad"><div style=3D"color:#9b99b0;direction:ltr;font-family:&#39=
;Open Sans&#39;,&#39;Helvetica Neue&#39;,Helvetica,Arial,sans-serif;font-si=
ze:12px;font-weight:400;letter-spacing:0;line-height:120%;text-align:center=
;mso-line-height-alt:14.399999999999999px"><p style=3D"margin:0">1776 Peach=
tree St. NW Suite 200N, Atlanta, GA, USA</p></div></td></tr></tbody></table=
><table class=3D"social_block block-3" width=3D"100%" border=3D"0" cellpadd=
ing=3D"16" cellspacing=3D"0" role=3D"presentation" style=3D"mso-table-lspac=
e:0;mso-table-rspace:0;mso-hide:all;display:none;max-height:0;overflow:hidd=
en"><tbody><tr><td class=3D"pad"><div class=3D"alignment" align=3D"center">=
<table class=3D"social-table" width=3D"228.52307692307693px" border=3D"0" c=
ellpadding=3D"0" cellspacing=3D"0" role=3D"presentation" style=3D"mso-table=
-lspace:0;mso-table-rspace:0;mso-hide:all;max-height:0;overflow:hidden;disp=
lay:inline-block"><tbody><tr>
<td style=3D"padding:0 7px 0 7px"><a href=3D"https://e.customeriomail.com/e=
/c/eyJlbWFpbF9pZCI6ImRnVHR5UWdEQVBMZ0dfSGdHd0dPeGZMODVtN2U1RklZRzNGS3JrRT0i=
LCJocmVmIjoiaHR0cHM6Ly93d3cuZmFjZWJvb2suY29tL3Zpc2lseWFpIiwiaW50ZXJuYWwiOiJ=
lZGM5MDgwZmExMjVmMmUwMWIiLCJsaW5rX2lkIjozMH0/820c2ce742b2f8aa2d010704facea1=
b63d1b70cea2bc54b203624b7b04e25705" target=3D"_blank"><img src=3D"https://u=
serimg-assets.customeriomail.com/images/client-env-140525/1688377142020_%F0=
%9F%A6%86%20icon%20_Facebook%20v1_-min_01H4DHXAXQFVHK20VDTSFVV5E5.png" widt=
h=3D"31.50769230769231" height=3D"auto" alt=3D"Facebook" title=3D"Facebook"=
 style=3D"display:block;height:auto;border:0"/></a></td><td style=3D"paddin=
g:0 7px 0 7px">
<a href=3D"https://e.customeriomail.com/e/c/eyJlbWFpbF9pZCI6ImRnVHR5UWdEQVB=
MZ0dfSGdHd0dPeGZMODVtN2U1RklZRzNGS3JrRT0iLCJocmVmIjoiaHR0cHM6Ly93d3cuaW5zdG=
FncmFtLmNvbS92aXNpbHlhaS8iLCJpbnRlcm5hbCI6ImVkYzkwODBmYTEyNWYyZTAxYiIsImxpb=
mtfaWQiOjMxfQ/6b5abc95bd83bcbe33f6aacb8d3ca6149c8cb673b3202336b74811f4acdc5=
65f" target=3D"_blank"><img src=3D"https://userimg-assets.customeriomail.co=
m/images/client-env-140525/1688377141060_%F0%9F%A6%86%20icon%20_Instagram_-=
min_01H4DHX9ZKY5Y9G0D4FWYRV8N5.png" width=3D"32" height=3D"auto" alt=3D"Ins=
tagram" title=3D"Instagram" style=3D"display:block;height:auto;border:0"/><=
/a></td><td style=3D"padding:0 7px 0 7px"><a href=3D"https://e.customerioma=
il.com/e/c/eyJlbWFpbF9pZCI6ImRnVHR5UWdEQVBMZ0dfSGdHd0dPeGZMODVtN2U1RklZRzNG=
S3JrRT0iLCJocmVmIjoiaHR0cHM6Ly93d3cubGlua2VkaW4uY29tL2NvbXBhbnkvdmlzaWx5YWk=
vIiwiaW50ZXJuYWwiOiJlZGM5MDgwZmExMjVmMmUwMWIiLCJsaW5rX2lkIjozfQ/c9c29d3034b=
2bbd4b1837805e87601b2885e3facb26b4533a47ca0ca766c04a6" target=3D"_blank"><i=
mg src=3D"https://userimg-assets.customeriomail.com/images/client-env-14052=
5/1688377140084_%F0%9F%A6%86%20icon%20_Linkedin_-min_01H4DHX916K2HNENF8P226=
XTXM.png" width=3D"31.50769230769231" height=3D"auto" alt=3D"LinkedIn" titl=
e=3D"LinkedIn" style=3D"display:block;height:auto;border:0"/></a></td><td s=
tyle=3D"padding:0 7px 0 7px"><a href=3D"https://e.customeriomail.com/e/c/ey=
JlbWFpbF9pZCI6ImRnVHR5UWdEQVBMZ0dfSGdHd0dPeGZMODVtN2U1RklZRzNGS3JrRT0iLCJoc=
mVmIjoiaHR0cHM6Ly90d2l0dGVyLmNvbS9pL2Zsb3cvbG9naW4_cmVkaXJlY3RfYWZ0ZXJfbG9n=
aW49JTJGdmlzaWx5YWkiLCJpbnRlcm5hbCI6ImVkYzkwODBmYTEyNWYyZTAxYiIsImxpbmtfaWQ=
iOjMyfQ/9c655d6a3057e252c826be172c253ddbccea6e68a6ab61981273465f3dea41a4" t=
arget=3D"_blank"><img src=3D"https://userimg-assets.customeriomail.com/imag=
es/client-env-140525/1688377142829_%F0%9F%A6%86%20icon%20_Twitter_-min_01H4=
DHXBPYQF8J1KT5BWV0ZPEY.png" width=3D"31.50769230769231" height=3D"auto" alt=
=3D"Twitter" title=3D"Twitter" style=3D"display:block;height:auto;border:0"=
/></a></td><td style=3D"padding:0 7px 0 7px"><a href=3D"https://e.customeri=
omail.com/e/c/eyJlbWFpbF9pZCI6ImRnVHR5UWdEQVBMZ0dfSGdHd0dPeGZMODVtN2U1RklZR=
zNGS3JrRT0iLCJocmVmIjoiaHR0cHM6Ly93d3cudmlzaWx5LmFpLyIsImludGVybmFsIjoiZWRj=
OTA4MGZhMTI1ZjJlMDFiIiwibGlua19pZCI6MzN9/789693e2f759ab3d796d6c519d7de5e302=
0ac653d2cb577791f2b398339f96fa" target=3D"_blank"><img src=3D"https://useri=
mg-assets.customeriomail.com/images/client-env-140525/1688373698143_Visily%=
20icon-min_01H4DEM7RB1W65875HDXQ8J1BS.png" width=3D"32" height=3D"auto" alt=
=3D"Visily" title=3D"Visily" style=3D"display:block;height:auto;border:0"/>=
</a></td></tr></tbody></table></div></td></tr></tbody></table><table class=
=3D"text_block block-4" width=3D"100%" border=3D"0" cellpadding=3D"10" cell=
spacing=3D"0" role=3D"presentation" style=3D"mso-table-lspace:0;mso-table-r=
space:0;word-break:break-word;mso-hide:all;display:none;max-height:0;overfl=
ow:hidden"><tbody><tr><td class=3D"pad"><div style=3D"font-family:sans-seri=
f"><div class=3D"" style=3D"font-size:12px;font-family:&#39;Open Sans&#39;,=
&#39;Helvetica Neue&#39;,Helvetica,Arial,sans-serif;mso-line-height-alt:14.=
399999999999999px;color:#9b99b0;line-height:1.2"><p style=3D"margin:0;mso-l=
ine-height-alt:14.399999999999999px"></p><div style=3D"font-size:14px;text-=
align:center">
<u><a href=3D"https://e.customeriomail.com/unsubscribe/dgTtyQgDAPLgG_HgGwGO=
xfL85m7e5FIYG3FKrkE=3D" target=3D"_blank" style=3D"text-decoration: underli=
ne; color: #9b99b0;" rel=3D"noopener">Unsubscribe</a></u></div><p style=3D"=
margin:0;mso-line-height-alt:14.399999999999999px"></p></div></div></td></t=
r></tbody></table></td></tr></tbody></table></td></tr></tbody></table><tabl=
e class=3D"row row-19 mobile_hide" align=3D"center" width=3D"100%" border=
=3D"0" cellpadding=3D"0" cellspacing=3D"0" role=3D"presentation" style=3D"m=
so-table-lspace:0;mso-table-rspace:0;background-color:#f1ecff"><tbody><tr><=
td><table class=3D"row-content stack" align=3D"center" border=3D"0" cellpad=
ding=3D"0" cellspacing=3D"0" role=3D"presentation" style=3D"mso-table-lspac=
e:0;mso-table-rspace:0;background-color:#f1ecff;color:#000;width:740px;marg=
in:0 auto" width=3D"740"><tbody><tr><td class=3D"column column-1" width=3D"=
100%" style=3D"mso-table-lspace:0;mso-table-rspace:0;font-weight:400;text-a=
lign:left;padding-bottom:5px;padding-left:40px;padding-right:40px;padding-t=
op:5px;vertical-align:top;border-top:0;border-right:0;border-bottom:0;borde=
r-left:0"><table class=3D"paragraph_block block-1" width=3D"100%" border=3D=
"0" cellpadding=3D"0" cellspacing=3D"0" role=3D"presentation" style=3D"mso-=
table-lspace:0;mso-table-rspace:0;word-break:break-word"><tbody><tr><td cla=
ss=3D"pad" style=3D"padding-bottom:10px;padding-left:10px;padding-right:10p=
x;padding-top:20px"><div style=3D"color:#12101a;direction:ltr;font-family:&=
#39;Open Sans&#39;,&#39;Helvetica Neue&#39;,Helvetica,Arial,sans-serif;font=
-size:12px;font-weight:400;letter-spacing:0;line-height:120%;text-align:cen=
ter;mso-line-height-alt:14.399999999999999px"><p style=3D"margin:0">
<strong>Visily</strong>, AI-powered app wireframing &amp; prototyping</p></=
div></td></tr></tbody></table><table class=3D"paragraph_block block-2" widt=
h=3D"100%" border=3D"0" cellpadding=3D"10" cellspacing=3D"0" role=3D"presen=
tation" style=3D"mso-table-lspace:0;mso-table-rspace:0;word-break:break-wor=
d"><tbody><tr><td class=3D"pad"><div style=3D"color:#9b99b0;direction:ltr;f=
ont-family:&#39;Open Sans&#39;,&#39;Helvetica Neue&#39;,Helvetica,Arial,san=
s-serif;font-size:12px;font-weight:400;letter-spacing:0;line-height:120%;te=
xt-align:center;mso-line-height-alt:14.399999999999999px"><p style=3D"margi=
n:0">1776 Peachtree St. NW Suite 200N, Atlanta, GA, USA</p></div></td></tr>=
</tbody></table><table class=3D"social_block block-3" width=3D"100%" border=
=3D"0" cellpadding=3D"16" cellspacing=3D"0" role=3D"presentation" style=3D"=
mso-table-lspace:0;mso-table-rspace:0"><tbody><tr><td class=3D"pad"><div cl=
ass=3D"alignment" align=3D"center"><table class=3D"social-table" width=3D"2=
28.52307692307693px" border=3D"0" cellpadding=3D"0" cellspacing=3D"0" role=
=3D"presentation" style=3D"mso-table-lspace:0;mso-table-rspace:0;display:in=
line-block"><tbody><tr><td style=3D"padding:0 7px 0 7px"><a href=3D"https:/=
/e.customeriomail.com/e/c/eyJlbWFpbF9pZCI6ImRnVHR5UWdEQVBMZ0dfSGdHd0dPeGZMO=
DVtN2U1RklZRzNGS3JrRT0iLCJocmVmIjoiaHR0cHM6Ly93d3cuZmFjZWJvb2suY29tL3Zpc2ls=
eWFpIiwiaW50ZXJuYWwiOiJlZGM5MDgwZmExMjVmMmUwMWIiLCJsaW5rX2lkIjozMH0/820c2ce=
742b2f8aa2d010704facea1b63d1b70cea2bc54b203624b7b04e25705" target=3D"_blank=
"><img src=3D"https://userimg-assets.customeriomail.com/images/client-env-1=
40525/1688377142020_%F0%9F%A6%86%20icon%20_Facebook%20v1_-min_01H4DHXAXQFVH=
K20VDTSFVV5E5.png" width=3D"31.50769230769231" height=3D"auto" alt=3D"Faceb=
ook" title=3D"Facebook" style=3D"display:block;height:auto;border:0"/></a><=
/td><td style=3D"padding:0 7px 0 7px"><a href=3D"https://e.customeriomail.c=
om/e/c/eyJlbWFpbF9pZCI6ImRnVHR5UWdEQVBMZ0dfSGdHd0dPeGZMODVtN2U1RklZRzNGS3Jr=
RT0iLCJocmVmIjoiaHR0cHM6Ly93d3cuaW5zdGFncmFtLmNvbS92aXNpbHlhaS8iLCJpbnRlcm5=
hbCI6ImVkYzkwODBmYTEyNWYyZTAxYiIsImxpbmtfaWQiOjMxfQ/6b5abc95bd83bcbe33f6aac=
b8d3ca6149c8cb673b3202336b74811f4acdc565f" target=3D"_blank"><img src=3D"ht=
tps://userimg-assets.customeriomail.com/images/client-env-140525/1688377141=
060_%F0%9F%A6%86%20icon%20_Instagram_-min_01H4DHX9ZKY5Y9G0D4FWYRV8N5.png" w=
idth=3D"32" height=3D"auto" alt=3D"Instagram" title=3D"Instagram" style=3D"=
display:block;height:auto;border:0"/></a></td><td style=3D"padding:0 7px 0 =
7px"><a href=3D"https://e.customeriomail.com/e/c/eyJlbWFpbF9pZCI6ImRnVHR5UW=
dEQVBMZ0dfSGdHd0dPeGZMODVtN2U1RklZRzNGS3JrRT0iLCJocmVmIjoiaHR0cHM6Ly93d3cub=
Glua2VkaW4uY29tL2NvbXBhbnkvdmlzaWx5YWkvIiwiaW50ZXJuYWwiOiJlZGM5MDgwZmExMjVm=
MmUwMWIiLCJsaW5rX2lkIjozfQ/c9c29d3034b2bbd4b1837805e87601b2885e3facb26b4533=
a47ca0ca766c04a6" target=3D"_blank"><img src=3D"https://userimg-assets.cust=
omeriomail.com/images/client-env-140525/1688377140084_%F0%9F%A6%86%20icon%2=
0_Linkedin_-min_01H4DHX916K2HNENF8P226XTXM.png" width=3D"31.50769230769231"=
 height=3D"auto" alt=3D"LinkedIn" title=3D"LinkedIn" style=3D"display:block=
;height:auto;border:0"/></a></td><td style=3D"padding:0 7px 0 7px"><a href=
=3D"https://e.customeriomail.com/e/c/eyJlbWFpbF9pZCI6ImRnVHR5UWdEQVBMZ0dfSG=
dHd0dPeGZMODVtN2U1RklZRzNGS3JrRT0iLCJocmVmIjoiaHR0cHM6Ly90d2l0dGVyLmNvbS9pL=
2Zsb3cvbG9naW4_cmVkaXJlY3RfYWZ0ZXJfbG9naW49JTJGdmlzaWx5YWkiLCJpbnRlcm5hbCI6=
ImVkYzkwODBmYTEyNWYyZTAxYiIsImxpbmtfaWQiOjMyfQ/9c655d6a3057e252c826be172c25=
3ddbccea6e68a6ab61981273465f3dea41a4" target=3D"_blank"><img src=3D"https:/=
/userimg-assets.customeriomail.com/images/client-env-140525/1688377142829_%=
F0%9F%A6%86%20icon%20_Twitter_-min_01H4DHXBPYQF8J1KT5BWV0ZPEY.png" width=3D=
"31.50769230769231" height=3D"auto" alt=3D"Twitter" title=3D"Twitter" style=
=3D"display:block;height:auto;border:0"/></a></td><td style=3D"padding:0 7p=
x 0 7px"><a href=3D"https://e.customeriomail.com/e/c/eyJlbWFpbF9pZCI6ImRnVH=
R5UWdEQVBMZ0dfSGdHd0dPeGZMODVtN2U1RklZRzNGS3JrRT0iLCJocmVmIjoiaHR0cHM6Ly93d=
3cudmlzaWx5LmFpLyIsImludGVybmFsIjoiZWRjOTA4MGZhMTI1ZjJlMDFiIiwibGlua19pZCI6=
MzN9/789693e2f759ab3d796d6c519d7de5e3020ac653d2cb577791f2b398339f96fa" targ=
et=3D"_blank"><img src=3D"https://userimg-assets.customeriomail.com/images/=
client-env-140525/1688373698143_Visily%20icon-min_01H4DEM7RB1W65875HDXQ8J1B=
S.png" width=3D"32" height=3D"auto" alt=3D"Visily" title=3D"Visily" style=
=3D"display:block;height:auto;border:0"/></a></td></tr></tbody></table></di=
v></td></tr></tbody></table><table class=3D"text_block block-4" width=3D"10=
0%" border=3D"0" cellpadding=3D"10" cellspacing=3D"0" role=3D"presentation"=
 style=3D"mso-table-lspace:0;mso-table-rspace:0;word-break:break-word"><tbo=
dy><tr><td class=3D"pad"><div style=3D"font-family:sans-serif"><div class=
=3D"" style=3D"font-size:12px;font-family:&#39;Open Sans&#39;,&#39;Helvetic=
a Neue&#39;,Helvetica,Arial,sans-serif;mso-line-height-alt:14.3999999999999=
99px;color:#9b99b0;line-height:1.2"><p style=3D"margin:0;mso-line-height-al=
t:14.399999999999999px"></p><div style=3D"font-size:14px;text-align:center"=
><u><a href=3D"https://e.customeriomail.com/unsubscribe/dgTtyQgDAPLgG_HgGwG=
OxfL85m7e5FIYG3FKrkE=3D" target=3D"_blank" style=3D"text-decoration: underl=
ine; color: #9b99b0;" rel=3D"noopener">Unsubscribe</a></u></div><p style=3D=
"margin:0;mso-line-height-alt:14.399999999999999px"></p></div></div></td></=
tr></tbody></table></td></tr></tbody></table></td>
</tr></tbody></table></td></tr></tbody></table><!-- End --><img src=3D"http=
s://e.customeriomail.com/e/o/eyJlbWFpbF9pZCI6ImRnVHR5UWdEQVBMZ0dfSGdHd0dPeG=
ZMODVtN2U1RklZRzNGS3JrRT0ifQ=3D=3D" style=3D"height: 1px !important; max-he=
ight: 1px !important; max-width: 1px !important; width: 1px !important; dis=
play: none !important;" alt=3D""/></body></html>
--25111ff57bae4f18f7cc15d8b3af0c32faaae62f3b52709a52f9bef15ce6--"""

msg = message_from_string(x)
for part in msg.walk():
    if part.get_content_type() == "text/html":
        print(part.get_payload())
    # print(part.get_content_type())

msg.get_
