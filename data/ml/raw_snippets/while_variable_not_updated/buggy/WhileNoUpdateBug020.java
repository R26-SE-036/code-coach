package data.ml.raw_snippets.while_variable_not_updated.buggy;

public class WhileNoUpdateBug020 {
    static void launch(int countdown) {
        int display = countdown;
        while (countdown > 0) {
            System.out.println(display);
            display--;
        }
    }
}
