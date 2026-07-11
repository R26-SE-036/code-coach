public class GenArrayIndexFix129 {
    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static int lastOf(int[] ratings) {
        return ratings[ratings.length - 1];
    }
}
