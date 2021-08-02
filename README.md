# PowerScout

A security-oriented power delivery network modeling framework.

<!-- PROJECT LOGO -->
  <p align="left">
    <a href="https://github.com/xz-group/PowerScout/issues">Report Bug</a>
    ·
    <a href="https://github.com/xz-group/PowerScout/issues">Request Feature</a>
  </p>

---



## What's News

Version 1.0

This is the initial release of the PowerScout with features that are fully tested.



<!-- ABOUT THE PROJECT -->
## About The Project

The growing complexity of modern electronic systems often
leads to the design of more sophisticated power delivery networks
(PDNs). Similar to other system-level shared resources, the on-board PDN
unintentionally introduces side channels across design layers and voltage
domains, despite the fact that PDNs are not part of the functional design.

Thus, we develop PowerScout, a security-oriented PDN simulation framework that unifies
the modeling of different PDN-based side-channel attacks. PowerScout
performs fast nodal analysis of complex PDNs at the system level to
quantitatively evaluate the severity of side-channel vulnerabilities.



<!-- GETTING STARTED -->
## Getting Started

### Prerequisites
+ PowerScout is based on **Ngspice** circuit simulator. To install:
   + For Windows: 
   Unzip `ngspice-34_dll_64.zip` to `C:\Program Files`. Make sure the path of `ngspice.dll` file is:
   
   ```shell
   C:\Program Files\Spice64_dll\dll-vs\ngspice.dll
   ```
   + For Linux: please refer [Ngspice manual](http://ngspice.sourceforge.net/docs/ngspice-manual.pdf) for the detailed instructions.

### Installation
+ Clone the repo
```bash
git clone https://github.com/xz-group/PowerScout.git
```

<!-- USAGE EXAMPLES -->
## Get Started


## Advanced Usage


<!-- ROADMAP -->
## Roadmap

See the [open issues](https://github.com/xz-group/PowerScout/issues/issues) for a list of proposed features (and known issues).


## Contributiors
The PowerScout is mainly developed by *Huifeng Zhu* and *[Dr.Silvia Zhang](https://xzgroup.wustl.edu/people/xuan-silvia-zhang/)* from *Washington University in St.Louis*; *[Dr.Yier Jin](http://jin.ece.ufl.edu/)* from the *University of Florida*; and *[Dr.Xiaolong Guo](https://www.ece.k-state.edu/people/faculty/guo/)* from *Kansas State University*.

We also appreciate the efforts of below contributors: 

## How to Refer to PowerScout?
If you are using PowerScout, please cite our official paper. 
You can find the paper in the website of IEEE: [link](https://ieeexplore.ieee.org/abstract/document/9358263).

A typical BibTeX citation would be, for example:
```
@inproceedings{zhu2020powerscout,
  title={PowerScout: A Security-Oriented Power Delivery Network Modeling Framework for Cross-Domain Side-Channel Analysis},
  author={Zhu, Huifeng and Guo, Xiaolong and Jin, Yier and Zhang, Xuan},
  booktitle={2020 Asian Hardware Oriented Security and Trust Symposium (AsianHOST)},
  pages={1--6},
  year={2020},
  organization={IEEE}
}
```
## Get Feedback
Feel free to contact us if you have questions about PowerScout: **Huifeng Zhu (zhuhuifeng AT wustl DOT edu)**.

## License
See `LICENSE` for more information.