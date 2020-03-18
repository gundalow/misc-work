
Here's some steps to test the build process:

::
    python3.8 -m pip install -r build-acd-requirements.txt --user
    mkdir built
    python3.8 build-acd.py new-acd 2.10.0 --dest-dir built
    python3.8 build-acd.py build-single 2.10.0 --build-file built/acd-2.10.build --dest-dir built
    # Create a collection that can be installed to pull in all of the collections
    python3.8 build-acd.py build-collection 2.10.0 --deps-file built/acd-2.10.0.deps --dest-dir built

    # Once this is uploaded to pypi or testpypi, we can test installing the ansible-2.10.0.tar.gz
    # using pip to resolve the requirement on ansible-base
    python -m pip install --user git+https://github.com/ansible/ansible.git#egg=ansible-base
    python -m pip install --user built/ansible-2.10.0.tar.gz

    ansible -m ansible.posix.synchronize -a 'src=/etc/skel dest=/var/tmp/testing-acd' localhost
