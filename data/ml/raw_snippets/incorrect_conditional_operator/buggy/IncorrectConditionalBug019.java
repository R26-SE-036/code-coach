package data.ml.raw_snippets.incorrect_conditional_operator.buggy;

public class IncorrectConditionalBug019 {
    public void checkCapacity(int size, int capacity) {
        boolean full = false;
        if (full = size >= capacity) {
            System.out.println("At full capacity");
        }
    }
}
