package data.ml.raw_snippets.while_variable_not_updated.buggy;

public class WhileNoUpdateBug018 {
    static void serveQueue(int waiting) {
        while (waiting > 0) {
            System.out.println("Serving customer, " + waiting + " left");
        }
        System.out.println("Queue empty");
    }
}
