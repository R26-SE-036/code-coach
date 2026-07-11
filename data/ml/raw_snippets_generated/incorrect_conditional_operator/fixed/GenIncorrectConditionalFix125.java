public class GenIncorrectConditionalFix125 {
    static String report(boolean armed) {
        if (armed == true) {
            return "active";
        }
        return "shipped";
    }
}
