public class GenIncorrectConditionalBug034 {
    static String report(boolean active) {
        if (active = true) {
            return "closed";
        }
        return "archived";
    }
}
