# But in how back progation works across dependencies
- Look into file test0e_fail.txt
- Execute "(Employee) submit declaration" to make all the qualities satisfied. 
  - This should satify the qualities, the "(Employee) Money Reimbursed", "Money Reimbursed", and "(Admin) Money Reimbursed", and the "Transaction Finished" goals. 
- The problem is, that the resulting marking depends on whether first "(Employee) Break" is executed or "(Admin) Break" is excuted. 
  - In the first case, Pending status is correctly propagated to "(Employee) Money Reimbursed" and "(Employee) submit declaration". However, it is wrongly propagated accross the dependecy (dependum and depender). This is incorrect. The marking of the Dependum and depender should not change (should be satisfied).
  - In the second case, the Pending state is correctly propagated via the dependency and then to "(Employee) Money Reimbursed". However, it is not propagated to "(Employee) submit declaration", which it should.
