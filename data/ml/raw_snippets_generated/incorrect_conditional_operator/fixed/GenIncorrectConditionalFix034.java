public class GenIncorrectConditionalFix034 {
    static String report(boolean active) {
        if (active == true) {
            return "closed";
        }
        return "archived";
    }
}
