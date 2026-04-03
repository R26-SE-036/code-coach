package data.ml.raw_snippets.incorrect_conditional_operator.buggy;

public class IncorrectConditionalBug026 {
    public void checkTimeout(long elapsed, long limit) {
        boolean timedOut = false;
        if (timedOut = elapsed > limit) {
            System.out.println("Request timed out");
        }
    }
}
