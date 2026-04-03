package data.ml.raw_snippets.incorrect_conditional_operator.buggy;

public class IncorrectConditionalBug012 {
    public void checkCount(int count) {
        if (count = 0) {
            System.out.println("Empty");
        }
    }
}
