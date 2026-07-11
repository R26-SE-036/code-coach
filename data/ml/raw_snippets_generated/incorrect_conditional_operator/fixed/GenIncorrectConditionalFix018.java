public class GenIncorrectConditionalFix018 {
    static String report(boolean armed) {
        if (armed == true) {
            return "new";
        }
        return "queued";
    }
}
