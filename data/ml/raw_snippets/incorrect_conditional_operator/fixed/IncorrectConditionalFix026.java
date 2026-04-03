package data.ml.raw_snippets.incorrect_conditional_operator.fixed;

public class IncorrectConditionalFix026 {
    public void checkTimeout(long elapsed, long limit) {
        boolean timedOut = elapsed > limit;
        if (timedOut) {
            System.out.println("Request timed out");
        }
    }
}
