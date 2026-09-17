package data.ml.raw_snippets.while_variable_not_updated.buggy;

public class WhileNoUpdateBug016 {
    public static void main(String[] args) {
        int battery = 100;
        int hours = 0;
        while (battery > 20) {
            hours++;
            System.out.println("Hour " + hours + ": " + battery + "%");
        }
    }
}
