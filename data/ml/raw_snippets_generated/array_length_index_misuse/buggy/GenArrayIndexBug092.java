public class GenArrayIndexBug092 {
    static int lastOf(int[] ages) {
        return ages[ages.length];
    }

    static boolean isEven1(int count) {
        return count % 2 == 0;
    }
}
