public class GenArrayIndexBug145 {
    static void stampLast(int[] ages, int value) {
        ages[ages.length] = value;
    }

    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }
}
