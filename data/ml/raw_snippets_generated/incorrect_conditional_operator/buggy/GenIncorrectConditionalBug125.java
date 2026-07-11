public class GenIncorrectConditionalBug125 {
    static String report(boolean armed) {
        if (armed = true) {
            return "active";
        }
        return "shipped";
    }
}
