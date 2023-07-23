# Sybil.ai - Polkadot APAC Hackathon
<a name="readme-top"></a>

<!-- PROJECT SHIELDS -->
<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->
[![Contributors][contributors-shield]][contributors-url]
[![MIT License][license-shield]][license-url]


<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/othneildrew/Best-README-Template">
    <img src="https://github.com/Yukino2002/Polkadot-Seoul/assets/66853318/81e96ae8-8c0b-4014-b8ef-d32d209c0f9a" alt="Logo" width="80" height="80">
  </a>

  <h3 align="center">Sybil.ai</h3>

  <p align="center">
    Simplifying blockchain interaction for everyone.
    <br />
    <a href="https://github.com/Yukino2002/Polkadot-Seoul/"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="Demo link">View Demo</a>
    ·
    <a href="https://github.com/Yukino2002/Polkadot-Seoul/issues">Report Bug</a>
    ·
    <a href="https://github.com/Yukino2002/Polkadot-Seoul/issues">Request Feature</a>
  </p>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#demo">Demo</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>

- Video Demo Link: 
- Live at: [http://www.sybilai.live](http://www.sybilai.live/)

 Note: You can use any google account to sign in but if you want a demo account here is a demo google account: 
 
- username: demoforsybilai@gmail.com
- password: demo@123

<!-- ABOUT THE PROJECT -->
## About The Project

![Product Name Screen Shot](https://github.com/Yukino2002/Polkadot-Seoul/assets/66853318/57317f4a-4350-42ce-8800-018260cb1512)


Sybil.ai, developed by Team GamerBroz, is a chatbot interface designed to offer seamless interaction with the Polkadot blockchain. By leveraging cutting-edge technologies and smart integrations, it simplifies the complexities of blockchain transactions and contract management, making it accessible to both technical and non-technical users alike.

Current chatbot features:
* Send and query balances
* Access transfer details
* Compile, deploy, and execute ink! contracts
* Reference Polkadot/Substrate documentation
* Interact with on-chain contracts, including ERC20 and NFT functions. 


<p align="right">(<a href="#readme-top">back to top</a>)</p>



### Built With

* [Next.js][Next-url]
* [TailwindCSS](https://tailwindcss.com/)
* [Firebase](https://firebase.google.com/)
* [OpenAI API](https://openai.com/)
* [Langchain](https://python.langchain.com/docs/get_started/introduction.html)
* [Deeplake](https://python.langchain.com/docs/integrations/deeplake)
* [substrate-interface](https://pypi.org/project/substrate-interface/)


<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- GETTING STARTED -->
## Getting Started
First, clone this repo using git onto your local machine. 
* git
  ```sh
  git clone https://github.com/Yukino2002/Polkadot-Seoul.git
  ```
The following instructions will help you set up the backend and frontend.

### Prerequisites

This is an example of how to list things you need to use the software and how to install them.
* npm
  ```sh
  npm install npm@latest -g
  ```
* pip
  ```sh
  curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
  python get-pip.py
  ```

### Installation

_First, let's set up the frontend for the project_

1. Go to the Polkadot-Seoul directory after cloning
  ```sh
  cd Polkadot-Seoul
  ```
2. Now navigate to the frontend directory
  ```sh
  cd frontend
  ```
3. Install NPM packages
   ```sh
   npm i
   ```
4. Make a `.env` file in the top-level directory and follow the template:
   ```js
   GOOGLE_ID=
   GOOGLE_SECRET=
   NEXTAUTH_URL=http://localhost:3000/
   NEXTAUTH_SECRET=SuperSecret
   FIREBASE_SERVICE_ACCOUNT_KEY=
   ```
5. Run the development server
   ```sh
   npm run dev
   ```
6. Now you can run the frontend on http://localhost:3000/

_In order to setup the backend follow the steps shown below_

1. Come back to the Polkadot-Seoul directory if you are not already in it
  ```sh
  cd ..
  ```
2. Now navigate to the backend directory
  ```sh
  cd backend-flask
  ```
3. Install python packages
   ```sh
   pip install -r requirements.txt
   ```
4. Make a `.env` file in the top-level directory and follow the template:
   ```js
   API_KEY=
   OPENAI_API_KEY=
   ACTIVELOOP_TOKEN=
   ```
5. Run the Python server
   ```sh
   python3 websockets.py
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- USAGE EXAMPLES -->
## Demo

- Video Demo Link: 
- Live at: [sybilai.live](http://www.sybilai.live/)

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTACT -->
## Contact

- Asim Jawahir - [@AsimJawahir](https://twitter.com/AsimJawahir) - asimjawahir123@gmail.com 
- Pratik Jallan - pratikjalan11@gmail.com
- Sai Leela Rahul Pujari - [@therahulpujari](https://twitter.com/therahulpujari) - rahulpujari2919@gmail.com 


Project Link: [https://github.com/Yukino2002/Polkadot-Seoul](https://github.com/Yukino2002/Polkadot-Seoul)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ACKNOWLEDGMENTS
## Acknowledgments

Use this space to list resources you find helpful and would like to give credit to. I've included a few of my favorites to kick things off!

* [Choose an Open Source License](https://choosealicense.com)
* [GitHub Emoji Cheat Sheet](https://www.webpagefx.com/tools/emoji-cheat-sheet)
* [Malven's Flexbox Cheatsheet](https://flexbox.malven.co/)
* [Malven's Grid Cheatsheet](https://grid.malven.co/)
* [Img Shields](https://shields.io)
* [GitHub Pages](https://pages.github.com)
* [Font Awesome](https://fontawesome.com)
* [React Icons](https://react-icons.github.io/react-icons/search)

<p align="right">(<a href="#readme-top">back to top</a>)</p>
 -->


<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/Yukino2002/Polkadot-Seoul.svg?style=for-the-badge
[contributors-url]: https://github.com/Yukino2002/Polkadot-Seoul/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/othneildrew/Best-README-Template.svg?style=for-the-badge
[forks-url]: https://github.com/othneildrew/Best-README-Template/network/members
[stars-shield]: https://img.shields.io/github/stars/othneildrew/Best-README-Template.svg?style=for-the-badge
[stars-url]: https://github.com/othneildrew/Best-README-Template/stargazers
[issues-shield]: https://img.shields.io/github/issues/othneildrew/Best-README-Template.svg?style=for-the-badge
[issues-url]: https://github.com/othneildrew/Best-README-Template/issues
[license-shield]: https://img.shields.io/github/license/othneildrew/Best-README-Template.svg?style=for-the-badge
[license-url]: https://github.com/othneildrew/Best-README-Template/blob/master/LICENSE.txt
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/othneildrew
[product-screenshot]: images/screenshot.png
[Next.js]: https://img.shields.io/badge/next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white
[Next-url]: https://nextjs.org/
