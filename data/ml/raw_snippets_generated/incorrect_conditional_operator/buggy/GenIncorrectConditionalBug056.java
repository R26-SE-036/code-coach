public class GenIncorrectConditionalBug056 {
    static String report(boolean armed) {
        if (armed = true) {
            return "paid";
        }
        return "closed";
    }
}
