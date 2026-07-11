public class GenArrayIndexFix145 {
    static void stampLast(int[] ages, int value) {
        ages[ages.length - 1] = value;
    }

    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }
}
