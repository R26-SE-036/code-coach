public class GenIncorrectConditionalFix100 {
    static String report(boolean loaded) {
        if (loaded == true) {
            return "final";
        }
        return "active";
    }
}
