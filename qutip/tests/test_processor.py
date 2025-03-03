import os

from numpy.testing import (
    assert_, run_module_suite, assert_allclose, assert_equal)
import numpy as np

from qutip.qip.device import Processor, LinearSpinChain
from qutip.states import basis
from qutip.operators import sigmaz, sigmax, sigmay, identity, destroy
from qutip.qip.operations.gates import hadamard_transform
from qutip.tensor import tensor
from qutip.solver import Options
from qutip.random_objects import rand_ket, rand_dm
from qutip.qip.noise import (
    DecoherenceNoise, RandomNoise, ControlAmpNoise)
from qutip.qip.qubits import qubit_states
from qutip.metrics import fidelity
from qutip.qip.pulse import Pulse
from qutip.qip.circuit import QubitCircuit

import pytest


class TestCircuitProcessor:
    def test_modify_ctrls(self):
        """
        Test for modifying Hamiltonian, add_control, remove_pulse
        """
        N = 2
        proc = Processor(N=N)
        proc.ctrls
        proc.add_control(sigmaz())
        assert_(tensor([sigmaz(), identity(2)]), proc.ctrls[0])
        proc.add_control(sigmax(), cyclic_permutation=True)
        assert_allclose(len(proc.ctrls), 3)
        assert_allclose(tensor([sigmax(), identity(2)]), proc.ctrls[1])
        assert_allclose(tensor([identity(2), sigmax()]), proc.ctrls[2])
        proc.add_control(sigmay(), targets=1)
        assert_allclose(tensor([identity(2), sigmay()]), proc.ctrls[3])
        proc.remove_pulse([0, 1, 2])
        assert_allclose(tensor([identity(2), sigmay()]), proc.ctrls[0])
        proc.remove_pulse(0)
        assert_allclose(len(proc.ctrls), 0)

    def test_save_read(self):
        """
        Test for saving and reading a pulse matrix
        """
        proc = Processor(N=2)
        proc.add_control(sigmaz(), cyclic_permutation=True)
        proc1 = Processor(N=2)
        proc1.add_control(sigmaz(), cyclic_permutation=True)
        proc2 = Processor(N=2)
        proc2.add_control(sigmaz(), cyclic_permutation=True)
        # TODO generalize to different tlist
        tlist = [0., 0.1, 0.2, 0.3, 0.4, 0.5]
        amp1 = np.arange(0, 5, 1)
        amp2 = np.arange(5, 0, -1)

        proc.pulses[0].tlist = tlist
        proc.pulses[0].coeff = amp1
        proc.pulses[1].tlist = tlist
        proc.pulses[1].coeff = amp2
        proc.save_coeff("qutip_test_CircuitProcessor.txt")
        proc1.read_coeff("qutip_test_CircuitProcessor.txt")
        os.remove("qutip_test_CircuitProcessor.txt")
        assert_allclose(proc1.get_full_coeffs(), proc.get_full_coeffs())
        assert_allclose(proc1.get_full_tlist(), proc.get_full_tlist())
        proc.save_coeff("qutip_test_CircuitProcessor.txt", inctime=False)
        proc2.read_coeff("qutip_test_CircuitProcessor.txt", inctime=False)
        proc2.set_all_tlist(tlist)
        os.remove("qutip_test_CircuitProcessor.txt")
        assert_allclose(proc2.get_full_coeffs(), proc.get_full_coeffs())

    def test_id_evolution(self):
        """
        Test for identity evolution
        """
        N = 1
        proc = Processor(N=N)
        init_state = rand_ket(2)
        tlist = [0., 1., 2.]
        proc.add_pulse(Pulse(identity(2), 0, tlist, False))
        result = proc.run_state(
            init_state, options=Options(store_final_state=True))
        global_phase = init_state.data[0, 0]/result.final_state.data[0, 0]
        assert_allclose(global_phase*result.final_state, init_state)

    def test_id_with_T1_T2(self):
        """
        Test for identity evolution with relaxation t1 and t2
        """
        # setup
        a = destroy(2)
        Hadamard = hadamard_transform(1)
        ex_state = basis(2, 1)
        mines_state = (basis(2, 1)-basis(2, 0)).unit()
        end_time = 2.
        tlist = np.arange(0, end_time + 0.02, 0.02)
        t1 = 1.
        t2 = 0.5

        # test t1
        test = Processor(1, t1=t1)
        # zero ham evolution
        test.add_pulse(Pulse(identity(2), 0, tlist, False))
        result = test.run_state(ex_state, e_ops=[a.dag()*a])
        assert_allclose(
            result.expect[0][-1], np.exp(-1./t1*end_time),
            rtol=1e-5, err_msg="Error in t1 time simulation")

        # test t2
        test = Processor(1, t2=t2)
        test.add_pulse(Pulse(identity(2), 0, tlist, False))
        result = test.run_state(
            init_state=mines_state, e_ops=[Hadamard*a.dag()*a*Hadamard])
        assert_allclose(
            result.expect[0][-1], np.exp(-1./t2*end_time)*0.5+0.5,
            rtol=1e-5, err_msg="Error in t2 time simulation")

        # test t1 and t2
        t1 = np.random.rand(1) + 0.5
        t2 = np.random.rand(1) * 0.5 + 0.5
        test = Processor(1, t1=t1, t2=t2)
        test.add_pulse(Pulse(identity(2), 0, tlist, False))
        result = test.run_state(
            init_state=mines_state, e_ops=[Hadamard*a.dag()*a*Hadamard])
        assert_allclose(
            result.expect[0][-1], np.exp(-1./t2*end_time)*0.5+0.5,
            rtol=1e-5,
            err_msg="Error in t1 & t2 simulation, "
                    "with t1={} and t2={}".format(t1, t2))

    def testPlot(self):
        """
        Test for plotting functions
        """
        try:
            import matplotlib.pyplot as plt
        except Exception:
            return True
        # step_func
        tlist = np.linspace(0., 2*np.pi, 20)
        processor = Processor(N=1, spline_kind="step_func")
        processor.add_control(sigmaz())
        processor.pulses[0].tlist = tlist
        processor.pulses[0].coeff = np.array([np.sin(t) for t in tlist])
        fig, _ = processor.plot_pulses()
        # testing under Xvfb with pytest-xvfb complains if figure windows are
        # left open, so we politely close it:
        plt.close(fig)

        # cubic spline
        tlist = np.linspace(0., 2*np.pi, 20)
        processor = Processor(N=1, spline_kind="cubic")
        processor.add_control(sigmaz())
        processor.pulses[0].tlist = tlist
        processor.pulses[0].coeff = np.array([np.sin(t) for t in tlist])
        fig, _ = processor.plot_pulses()
        # testing under Xvfb with pytest-xvfb complains if figure windows are
        # left open, so we politely close it:
        plt.close(fig)

    def testSpline(self):
        """
        Test if the spline kind is correctly transfered into
        the arguments in QobjEvo
        """
        tlist = np.array([1, 2, 3, 4, 5, 6], dtype=float)
        coeff = np.array([1, 1, 1, 1, 1, 1], dtype=float)
        processor = Processor(N=1, spline_kind="step_func")
        processor.add_control(sigmaz())
        processor.pulses[0].tlist = tlist
        processor.pulses[0].coeff = coeff

        ideal_qobjevo, _ = processor.get_qobjevo(noisy=False)
        assert_(ideal_qobjevo.args["_step_func_coeff"])
        noisy_qobjevo, c_ops = processor.get_qobjevo(noisy=True)
        assert_(noisy_qobjevo.args["_step_func_coeff"])
        processor.T1 = 100.
        processor.add_noise(ControlAmpNoise(coeff=coeff, tlist=tlist))
        noisy_qobjevo, c_ops = processor.get_qobjevo(noisy=True)
        assert_(noisy_qobjevo.args["_step_func_coeff"])

        tlist = np.array([1, 2, 3, 4, 5, 6], dtype=float)
        coeff = np.array([1, 1, 1, 1, 1, 1], dtype=float)
        processor = Processor(N=1, spline_kind="cubic")
        processor.add_control(sigmaz())
        processor.pulses[0].tlist = tlist
        processor.pulses[0].coeff = coeff

        ideal_qobjevo, _ = processor.get_qobjevo(noisy=False)
        assert_(not ideal_qobjevo.args["_step_func_coeff"])
        noisy_qobjevo, c_ops = processor.get_qobjevo(noisy=True)
        assert_(not noisy_qobjevo.args["_step_func_coeff"])
        processor.T1 = 100.
        processor.add_noise(ControlAmpNoise(coeff=coeff, tlist=tlist))
        noisy_qobjevo, c_ops = processor.get_qobjevo(noisy=True)
        assert_(not noisy_qobjevo.args["_step_func_coeff"])

    def testGetObjevo(self):
        tlist = np.array([1, 2, 3, 4, 5, 6], dtype=float)
        coeff = np.array([1, 1, 1, 1, 1, 1], dtype=float)
        processor = Processor(N=1)
        processor.add_control(sigmaz())
        processor.pulses[0].tlist = tlist
        processor.pulses[0].coeff = coeff

        # without noise
        unitary_qobjevo, _ = processor.get_qobjevo(
            args={"test": True}, noisy=False)
        assert_allclose(unitary_qobjevo.ops[0].qobj, sigmaz())
        assert_allclose(unitary_qobjevo.tlist, tlist)
        assert_allclose(unitary_qobjevo.ops[0].coeff, coeff[0])
        assert_(unitary_qobjevo.args["test"],
                msg="Arguments not correctly passed on")

        # with decoherence noise
        dec_noise = DecoherenceNoise(
            c_ops=sigmax(), coeff=coeff, tlist=tlist)
        processor.add_noise(dec_noise)
        assert_equal(unitary_qobjevo.to_list(),
                     processor.get_qobjevo(noisy=False)[0].to_list())

        noisy_qobjevo, c_ops = processor.get_qobjevo(
            args={"test": True}, noisy=True)
        assert_(noisy_qobjevo.args["_step_func_coeff"],
                msg="Spline type not correctly passed on")
        assert_(noisy_qobjevo.args["test"],
                msg="Arguments not correctly passed on")
        assert_(sigmaz() in [pair[0] for pair in noisy_qobjevo.to_list()])
        assert_equal(c_ops[0].ops[0].qobj, sigmax())
        assert_equal(c_ops[0].tlist, tlist)

        # with amplitude noise
        processor = Processor(N=1, spline_kind="cubic")
        processor.add_control(sigmaz())
        tlist = np.linspace(1, 6, int(5/0.2))
        coeff = np.random.rand(len(tlist))
        processor.pulses[0].tlist = tlist
        processor.pulses[0].coeff = coeff

        amp_noise = ControlAmpNoise(coeff=coeff, tlist=tlist)
        processor.add_noise(amp_noise)
        noisy_qobjevo, c_ops = processor.get_qobjevo(
            args={"test": True}, noisy=True)
        assert_(not noisy_qobjevo.args["_step_func_coeff"],
                msg="Spline type not correctly passed on")
        assert_(noisy_qobjevo.args["test"],
                msg="Arguments not correctly passed on")
        assert_equal(len(noisy_qobjevo.ops), 2)
        assert_equal(sigmaz(), noisy_qobjevo.ops[0].qobj)
        assert_allclose(coeff, noisy_qobjevo.ops[0].coeff, rtol=1.e-10)

    def testNoise(self):
        """
        Test for Processor with noise
        """
        # setup and fidelity without noise
        init_state = qubit_states(2, [0, 0, 0, 0])
        tlist = np.array([0., np.pi/2.])
        a = destroy(2)
        proc = Processor(N=2)
        proc.add_control(sigmax(), targets=1)
        proc.pulses[0].tlist = tlist
        proc.pulses[0].coeff = np.array([1])
        result = proc.run_state(init_state=init_state)
        assert_allclose(
            fidelity(result.states[-1], qubit_states(2, [0, 1, 0, 0])),
            1, rtol=1.e-7)

        # decoherence noise
        dec_noise = DecoherenceNoise([0.25*a], targets=1)
        proc.add_noise(dec_noise)
        result = proc.run_state(init_state=init_state)
        assert_allclose(
            fidelity(result.states[-1], qubit_states(2, [0, 1, 0, 0])),
            0.981852, rtol=1.e-3)

        # white random noise
        proc.noise = []
        white_noise = RandomNoise(0.2, np.random.normal, loc=0.1, scale=0.1)
        proc.add_noise(white_noise)
        result = proc.run_state(init_state=init_state)

    def testMultiLevelSystem(self):
        """
        Test for processor with multi-level system
        """
        N = 2
        proc = Processor(N=N, dims=[2, 3])
        proc.add_control(tensor(sigmaz(), rand_dm(3, density=1.)))
        proc.pulses[0].coeff = np.array([1, 2])
        proc.pulses[0].tlist = np.array([0., 1., 2])
        proc.run_state(init_state=tensor([basis(2, 0), basis(3, 1)]))

    def testDrift(self):
        """
        Test for the drift Hamiltonian
        """
        processor = Processor(N=1)
        processor.add_drift(sigmax() / 2, 0)
        tlist = np.array([0., np.pi, 2*np.pi, 3*np.pi])
        processor.add_pulse(Pulse(None, None, tlist, False))
        ideal_qobjevo, _ = processor.get_qobjevo(noisy=True)
        assert_equal(ideal_qobjevo.cte, sigmax() / 2)

        init_state = basis(2)
        propagators = processor.run_analytically()
        analytical_result = init_state
        for unitary in propagators:
            analytical_result = unitary * analytical_result
        fid = fidelity(sigmax() * init_state, analytical_result)
        assert((1 - fid) < 1.0e-6)

    def testChooseSolver(self):
        # setup and fidelity without noise
        init_state = qubit_states(2, [0, 0, 0, 0])
        tlist = np.array([0., np.pi/2.])
        a = destroy(2)
        proc = Processor(N=2)
        proc.add_control(sigmax(), targets=1)
        proc.pulses[0].tlist = tlist
        proc.pulses[0].coeff = np.array([1])
        result = proc.run_state(init_state=init_state, solver="mcsolve")
        assert_allclose(
            fidelity(result.states[-1], qubit_states(2, [0, 1, 0, 0])),
            1, rtol=1.e-7)

    def test_max_step_size(self):
        num_qubits = 2
        init_state = tensor([basis(2, 1), basis(2, 1)])
        qc = QubitCircuit(2)

        # ISWAP acts trivially on the initial states.
        # If no max_step are defined,
        # the solver will choose a step size too large
        # such that the X gate will be skipped.
        qc.add_gate("ISWAP", targets=[0, 1])
        qc.add_gate("ISWAP", targets=[0, 1])
        qc.add_gate("X", targets=[0])
        processor = LinearSpinChain(num_qubits)
        processor.load_circuit(qc)

        # No max_step
        final_state = processor.run_state(
            init_state, options=Options(max_step=10000) # too large max_step
        ).states[-1]
        expected_state = tensor([basis(2, 0), basis(2, 1)])
        assert pytest.approx(fidelity(final_state, expected_state), 0.001) == 0

        # With default max_step
        final_state = processor.run_state(init_state).states[-1]
        expected_state = tensor([basis(2, 0), basis(2, 1)])
        assert pytest.approx(fidelity(final_state, expected_state), 0.001) == 1


if __name__ == "__main__":
    run_module_suite()
