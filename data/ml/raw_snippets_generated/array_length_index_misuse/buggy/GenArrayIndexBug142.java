public class GenArrayIndexBug142 {
    static int lastOf(int[] sizes) {
        return sizes[sizes.length];
    }

    static int sum1(int[] ratings) {
        int total = 0;
        for (int i = 0; i < ratings.length; i++) {
            total += ratings[i];
        }
        return total;
    }

    static String describe2(int quota) {
        if (quota < 10) {
            return "low";
        } else if (quota > 50) {
            return "high";
        }
        return "medium";
    }
}
