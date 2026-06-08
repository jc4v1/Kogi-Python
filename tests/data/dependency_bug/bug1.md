# Bug 1 in how back progation works across dependencies
- Look into file test0e_fail.txt
- Execute "(Employee) submit declaration" to make all the qualities satisfied. 
- This should satify the qualities, the "(Employee) Money Reimbursed", "Money Reimbursed", and "(Admin) Money Reimbursed", and the "Transaction Finished" goals. 
- Then execute "(Employee) Break" is executed.
- Here, the Pending status is correctly propagated to "(Employee) Money Reimbursed" and "(Employee) submit declaration". However, it is wrongly propagated accross the dependecy (dependum and depender). This is incorrect. The marking of the Dependum and depender should not change (should be satisfied).
