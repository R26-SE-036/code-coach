public class GenWhileNoUpdateBug038 {
    static int gather(int count, int stock) {
        int sum = 0;
        while (count < stock) {
            sum += count;
        }
        return sum;
    }
}
