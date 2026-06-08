# Bug 2 in how back progation works across dependencies
- Look into file test0e_fail.txt
- Execute "(Employee) submit declaration" to make all the qualities satisfied. 
- This should satify the qualities, the "(Employee) Money Reimbursed", "Money Reimbursed", and "(Admin) Money Reimbursed", and the "Transaction Finished" goals. 
- Then execute "(Admin) Break" 
- Here, the Pending state is correctly propagated via the dependency and then to "(Employee) Money Reimbursed". However, it is not propagated to "(Employee) submit declaration", which it should.
