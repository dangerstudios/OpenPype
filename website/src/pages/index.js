import React from 'react';
import classnames from 'classnames';
import Layout from '@theme/Layout';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import useBaseUrl from '@docusaurus/useBaseUrl';
import styles from './styles.module.css';

import {BadgesSection} from '../components';

const services = [
  {
    title: <>Battle tested</>,
    description: (
      <>
        Designed, used, broken-in and validated in collaboration with many studios, who's artist have used it on projects ranging from commercials, to features.
      </>
    ),
  },
  {
    title: <>Supported</>,
    description: (
      <>
        OpenPYPE is developed and maintained by PYPE.club, a full-time, dedicated team of industry professionals, providing support and training to studios and artists.
      </>
    ),
  },
  {
    title: <>Extensible</>,
    description: (
      <>
        Project needs differ, clients differ and studios differ. OpenPype is designed to fit into your workflow and bend to your will. If a feature is missing, it can most probably be added. 
      </>
    ),
  },
  {
    title: <>Focused</>,
    description: (
      <>
        All OpenPype features have been added to solve specific needs during it's use in production. If something is obsolete, it is carefully deprecated, to keep the codebase lean and easier to maintain.
      </>
    ),
  },
];

const collab = [
  {
    title: 'Kredenc Studio',
    image: '/img/kredenc.png',
    infoLink: 'http://kredenc.studio'
  }, {
    title: 'Colorbleed',
    image: '/img/colorbleed_logo.png',
    infoLink: 'http://colorbleed.nl'
  }, {
    title: 'Bumpybox',
    image: '/img/bumpybox_bw.png',
    infoLink: 'http://bumpybox.com'
  }, {
    title: 'Moonshine',
    image: '/img/moonshine_logotype.png',
    infoLink: 'https://www.moonshine.tw/'
  }, {
    title: 'Clothcat Animation',
    image: '/img/clothcat.png',
    infoLink: 'https://www.clothcatanimation.com/'
  }
];

const clients = [
  {
    title: 'Imagine Studio',
    image: '/img/imagine_logo.png',
    infoLink: 'https://imaginestudio.cz/'
  }, {
    title: 'Dazzle Pictures',
    image: '/img/dazzle_CB.png',
    infoLink: 'https://www.dazzlepictures.net/'
  }, {
    title: '3DE',
    image: '/img/3de.png',
    infoLink: 'https://www.3de.com.pl/'
  }, {
    title: 'Incognito',
    image: '/img/client_incognito.png',
    infoLink: 'https://incognito.studio/'
  }, {
    title: 'Fourth Wall Animation',
    image: '/img/client_fourthwall_logo.png',
    infoLink: 'https://fourthwallanimation.com/'
  }, {
    title: 'The Scope Studio',
    image: '/img/thescope_logo.png',
    infoLink: 'https://thescope.studio/'
  }, {
    title: 'The Line Animation',
    image: '/img/thelineanimationlogo.png',
    infoLink: 'https://www.thelineanimation.com/'
  }, {
    title: 'Filmmore',
    image: '/img/filmmore_logotype_bw.png',
    infoLink: 'https://filmmore.nl/'
  },
  {
    title: 'Yowza Animation',
    image: '/img/client_yowza_logo.png',
    infoLink: 'https://yowzaanimation.com/'
  },
  {
      title: "Red Knuckles",
      image: "/img/redknuckles_logotype.png",
      infoLink: "https://www.redknuckles.co.uk/",
  },
  {
      title: "Orca Studios",
      image: "/img/orcastudios_logo.png",
      infoLink: "https://orcastudios.es/",
  }
];

function Service({imageUrl, title, description}) {
  const imgUrl = useBaseUrl(imageUrl);
  return (
    <div className={classnames('col col--3', styles.feature)}>
      <h3>{title}</h3>
      <p>{description}</p>
    </div>
  );
}

function Client({title, image, infoLink}) {
  const imgUrl = useBaseUrl(image);
  return (
    <a className="client" href={infoLink}>
      <img src={image} alt="" title={title}></img>
    </a>
  );
}

function Collaborator({title, image, infoLink}) {
  const imgUrl = useBaseUrl(image);
  return (
    <a className="collab" href={infoLink}>
      <img src={image} alt="" title={title}></img>
    </a>
  );
}

function Home() {
  const context = useDocusaurusContext();
  const {siteConfig = {}} = context;
  return (
    <Layout
      title={`${siteConfig.title}- pipeline with support`}
      description="VFX and Animation Pipeline for studios and remote teams <head />">
      <header className={classnames('hero hero--primary', styles.heroBanner)}>
        <div className="container">
          <h1 className={classnames(
            styles.hero__title,
          )}>
            <img src="img/logos/openpype_color.svg"></img>
          </h1>
          <h2><small className={styles.hero__subtitle}>{siteConfig.tagline}</small></h2>
          <div className={styles.buttons}>
            <Link
              className={classnames(
                'button button--outline button--primary',
                styles.button,
              )}
              to={'https://github.com/pypeclub/pype'}>
              Contribute
            </Link>
            <Link
              className={classnames(
                'button button--outline button--primary',
                styles.button,
              )}
              to={'mailto:info@pype.club'}>
              Get in touch
            </Link>
            <Link
              className={classnames(
                'button button--outline button--primary',
                styles.button,
              )}
              to={'https://discord.gg/sFNPWXG'}>
              Join our chat
            </Link>
            <Link
              className={classnames(
                'button button--outline button--primary',
                styles.button,
              )}
              to={'https://pype.club'}>
              Get Support
            </Link>
          </div>
          
          <p>
          OpenPYPE is developed, maintained and supported by <b><a href="https://pype.club">PYPE.club</a></b> </p>

        </div>
      </header>
      <main>

        {services && services.length && (
          <section className={classnames(styles.features,
                                        styles.center)}>
            <div className="container">
            {/* <h2>Services</h2> */}
              <div className="row">
                {services.map((props, idx) => (
                  <Service key={idx} {...props} />
                ))}
              </div>
            </div>
          </section>
        )}
        <section className={classnames(styles.features,
                                        "darkBackground")}>
          <div className="container">
            <div className={classnames('row')}>
              <div className="col col--6">
              <img src="/img/frontpage/undraw_mindmap.svg" />
              </div>
              <div className="col col--6">
                <h2>What is openPype?
                </h2>
                    <p>Open-source pipeline for visual effects and animation built on top of the <a href="https://getavalon.github.io/2.0/">Avalon </a> framework, expanding it with extra features and integrations. OpenPype connects your DCCs, asset database, project management and time tracking into a single system. It has a tight integration with Ftrack, but can also run independently or be integrated into a different project management solution.</p>

                    <p>
                    OpenPype provides a robust platform for your studio, without the worry of a vendor lock. You will always have full access to the source-code and your project database will run locally or in the cloud of your choice.
                    </p>
              </div>
            </div>
          </div>
        </section>

        <section className={classnames(styles.features)}>
          <div className="container">
            <div className={classnames('row',)}>
                <div className="col col--6">
                <h2>Why choose openPype?
                </h2>
                <p>
                Pipeline is the technical backbone of your production. It means, that whatever solution you use, it will cause vendor-lock to some extend. 
                You can mitigate this risk by developing purely in-house tools, however, that just shifts the problem from a software vendor to your developers. Sooner or later, you'll hit the limits of such solution. In-house tools tend to be undocumented, narrow focused and heavily dependent on a very few or even a single developer.
                </p>
                <p>
                OpenPYPE aims to solve these problems. It has dedicated and growing team of developers and support staff, that can provide the comfort of a commercial solution, while giving you the benefit of a full source-code access. You can build and deploy it yourself, or even fork and continue in-house if you're not happy about where openPYPE is heading in the future.
                </p>
                </div>
                <div className="col col--6">
                <img src="/img/frontpage/undraw_programming.svg" />
                </div>
            </div>
          </div>
        </section>
        
        <section className={classnames(styles.gallery, "center darkBackground")}>
          <div className="container">
              <h2>Integrations</h2>
              <div className={classnames('showcase',)}>
                <a className="link" href={useBaseUrl("features#maya")}>
                  <img src="/img/app_maya.png" alt="" title=""></img>
                  <span className="caption">Maya</span>
                </a>

                <a className="link" href={useBaseUrl("features#nuke")}>
                  <img src="/img/app_nuke.png" alt="" title=""></img>
                  <span className="caption">Nuke</span>
                </a>

                <a className="link" href={useBaseUrl("features#hiero")}>
                  <img src="/img/app_nuke.png" alt="" title=""></img>
                  <span className="caption">Nuke Studio</span>
                </a>

                <a className="link" href={useBaseUrl("features#hiero")}>
                  <img src="/img/app_hiero.png" alt="" title=""></img>
                  <span className="caption">Hiero</span>
                </a>

                <a className="link" href={useBaseUrl("features#houdini")}>
                  <img src="/img/app_houdini.png" alt="" title=""></img>
                  <span className="caption">Houdini</span>
                </a>

                <a className="link" href={useBaseUrl("features#blender")}>
                  <img src="/img/app_blender.png" alt="" title=""></img>
                  <span className="caption">Blender</span>
                </a>

                <a className="link" href={useBaseUrl("features#fusion")}>
                  <img src="/img/app_fusion.png" alt="" title=""></img>
                  <span className="caption">Fusion</span>
                </a>

                <a className="link" href={useBaseUrl("features#harmony")}>
                  <img src="/img/app_toonboom.png" alt="" title=""></img>
                  <span className="caption">Harmony</span>
                </a>

                <a className="link" href={useBaseUrl("features#photoshop")}>
                  <img src="/img/app_photoshop.png" alt="" title=""></img>
                  <span className="caption">Photoshop</span>
                </a>

                <a className="link" href={useBaseUrl("features#ftrack")}>
                  <img src="/img/app_ftrack.png" alt="" title=""></img>
                  <span className="caption">Ftrack</span>
                </a>

                <a className="link" href={useBaseUrl("features#clockify")}>
                  <img src="/img/app_clockify.png" alt="" title=""></img>
                  <span className="caption">Clockify</span>
                </a>

                <a className="link" href="">
                  <img src="/img/app_deadline.png" alt="" title=""></img>
                  <span className="caption">Deadline</span>
                </a>

                <a className="link" href="">
                  <img src="/img/app_muster.png" alt="" title=""></img>
                  <span className="caption">Muster</span>
                </a>

                <a className="link" href="">
                  <img src="/img/app_unreal.png" alt="" title=""></img>
                  <span className="caption">Unreal Engine (Beta)</span>
                </a>

                <a className="link" href="">
                  <img src="/img/app_aftereffects.png" alt="" title=""></img>
                  <span className="caption">After Effects</span>
                </a>

                <a className="link" href="">
                  <img src="/img/app_tvpaint.png" alt="" title=""></img>
                  <span className="caption">TV Paint</span>
                </a>

                <a className="link" href="">
                  <img src="/img/app_resolve.png" alt="" title=""></img>
                  <span className="caption">DaVinci Resolve (Alpha)</span>
                </a>

              </div>

              <p> <span>In development by us or a community of <a href="https://github.com/getavalon/core/pulls">avalon core</a> developers.</span></p>

              <div className={classnames('showcase',)}>

                <a className="link" href="">
                  <img src="/img/app_storyboardpro.svg" alt="" title=""></img>
                  <span className="caption">Storyboard Pro</span>
                </a>


              </div>
          </div>
        </section>

          <section className={styles.collaborators}>
            <div className="">
              <h2>Maintainers</h2>
              <div className="showcase">
                  <a className="pype_logo" href="https://pype.club">
                        <img src="/img/logos/pypeclub_black.svg" alt="" title="pype.club"></img>
                    </a>
              </div>
            </div>
          </section>

        {collab && collab.length && (
          <section className={styles.collaborators}>
            <div className="">
              <h2>Contributors</h2>
              <div className="showcase">
                {collab.map((props, idx) => (
                  <Collaborator key={idx} {...props} />
                ))}
              </div>
            </div>
          </section>
        )}


        {clients && clients.length && (
          <section className={styles.gallery}>
            <div className="container">
              <h2>Studios using openPYPE</h2>
              <div className="showcase">
                {clients.map((props, idx) => (
                  <Client key={idx} {...props} />
                ))}
              </div>
            </div>
          </section>
        )}



      <div className="container">
        <BadgesSection/>
      </div>


      </main>
    </Layout>
  );
}

export default Home;
