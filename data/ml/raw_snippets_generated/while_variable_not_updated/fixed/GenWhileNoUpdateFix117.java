public class GenWhileNoUpdateFix117 {
    static void printAll1(int[] marks) {
        for (int value : marks) {
            System.out.println(value);
        }
    }

    static int gather(int quota, int stock) {
        int sum = 0;
        while (quota < stock) {
            sum += quota;
            quota++;
        }
        return sum;
    }
}
