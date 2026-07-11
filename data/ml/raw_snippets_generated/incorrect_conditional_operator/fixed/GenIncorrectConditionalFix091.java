public class GenIncorrectConditionalFix091 {
    static String report(boolean active) {
        if (active == true) {
            return "queued";
        }
        return "archived";
    }
}
