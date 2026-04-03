package data.ml.raw_snippets.incorrect_conditional_operator.buggy;

public class IncorrectConditionalBug013 {
    public void processItem(Object item) {
        if (item = null) {
            System.out.println("Item is null");
        }
    }
}
