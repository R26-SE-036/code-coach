package data.ml.raw_snippets.incorrect_conditional_operator.buggy;

public class IncorrectConditionalBug028 {
    public void checkEvenSum(int a, int b) {
        boolean evenSum = false;
        if (evenSum = (a + b) % 2 == 0) {
            System.out.println("Even sum");
        }
    }
}
