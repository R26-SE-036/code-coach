public class GenArrayIndexBug013 {
    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static String describe2(int level) {
        if (level < 100) {
            return "low";
        } else if (level > 500) {
            return "high";
        }
        return "medium";
    }

    static int lastOf(int[] ages) {
        return ages[ages.length];
    }
}
